import threading
import cv2
from deepface import DeepFace
import os
import numpy as np
import time
import requests

class FaceDetection:
    def __init__(self):
        self.database = self.build_database()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.face_match = False
        self.reference_img = None
        self.counter = 0
        self.check_name = ""
        self.raspi_url = "http://192.168.137.225:5000"

    def build_database(self):
        image_dict = {}
        for image in os.listdir('face_image'):
            name = image.split('.')[0]
            reference_img = cv2.imread(f'face_image/{image}')
            image_dict[name] = reference_img
        return image_dict

    def verify_user(self, name):
        if name in self.database:
            print(f"You have access, {name}. Starting face detection...")
            self.reference_img = self.database[name]  # Load reference image for the provided name
            self.check_name = name
            return True
        else:
            print(f"{name}, you have no access to the store.")
            return False

    def check_face(self, frame):
        print("Enter here")
        try:
            result = DeepFace.verify(frame, self.reference_img.copy())
            print(result)
            if result['verified'] and result['distance'] <= 0.35:
                self.face_match = True
            else:
                self.face_match = False
        except ValueError:
            self.face_match = False
        print("Done")

    def start_detection(self):
        print("Enter 'S' to start the verification process: ")
        while True:
            start = input("")
            if start == 'S':
                break
        start_time = time.time()
        while (time.time() - start_time < 30):
            ret, frame = self.cap.read()
            if ret:
                if self.counter % 70 == 0:  # Check every 40th frame
                    try:
                        threading.Thread(target=self.check_face, daemon=True, args=(frame.copy(),)).start()
                    except ValueError:
                        pass
                self.counter += 1
                if self.face_match:
                    cv2.putText(frame, "MATCH!", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                    print("Face matched")
                    cv2.imshow("video", frame)
                    cv2.waitKey(1000)
                    return True
                else:
                    cv2.putText(frame, "NO MATCH!", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                    cv2.imshow("video", frame)
            key = cv2.waitKey(1)
            if key == ord("q"):
                break
        if not self.face_match:
            print("Timeout. Access denied.")
        self.cap.release()
        cv2.destroyAllWindows()
        return False

    def trigger_door(self, action):
        url = f'{self.raspi_url}/trigger_door'
        data = {'action': action}

        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                print(f"Door {action}ed successfully.")
            else:
                print(f"{response.json()['status']}")
        except Exception as e:
            print(f"Error communicating with Raspberry Pi: {e}")

    def detect_and_trigger(self, username):

        if self.verify_user(username):
            result = self.start_detection()
            if result:
                print("Face matched. Opening door...")
                self.trigger_door('open')
                
        # print("Looking for face...")
        # # Assuming fd.verify_user(username) returns True if face is recognized
        # if self.verify_user(username):  # This is where DeepFace detection is performed
        #     print(f"Face recognized for {username}. Opening door...")
        #     self.trigger_door('open')  # Trigger the door to open
        # else:
        #     print("Face not recognized.")


if __name__ == '__main__':
    fd = FaceDetection()
    username = input("Please enter the username to verify: ")
    fd.detect_and_trigger(username)