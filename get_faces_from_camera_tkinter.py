import dlib
import numpy as np
import cv2
import csv
import os
import shutil
import time
import logging
import tkinter as tk
from tkinter import font as tkFont
from PIL import Image, ImageTk

# Use frontal face detector of Dlib
detector = dlib.get_frontal_face_detector()

# Get face landmarks
predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')

# Use Dlib resnet50 model to get 128D face descriptor
face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")

class Face_Register:
    def __init__(self):
        self.current_frame_faces_cnt = 0  # cnt for counting faces in current frame
        self.existing_faces_cnt = 0  # cnt for counting saved faces
        self.ss_cnt = 0  # cnt for screen shots

        # Tkinter GUI
        self.win = tk.Tk()
        self.win.title("Student Face Registration System")

        # Please modify window size here if needed
        self.win.geometry("1080x720")

        # GUI right part (Camera)
        self.frame_right_camera = tk.Frame(self.win)
        self.label = tk.Label(self.frame_right_camera)
        self.label.pack()
        self.frame_right_camera.pack(side=tk.RIGHT)

        # GUI left part (Information)
        self.frame_left_info = tk.Frame(self.win)
        self.label_cnt_face_in_database = tk.Label(self.frame_left_info, text=str(self.existing_faces_cnt))
        self.label_fps_info = tk.Label(self.frame_left_info, text="")
        self.input_name = tk.Entry(self.frame_left_info)
        self.input_course = tk.StringVar(self.frame_left_info)
        self.input_academic_year = tk.StringVar(self.frame_left_info)
        self.input_gender = tk.StringVar(self.frame_left_info)
        self.input_roll = tk.Entry(self.frame_left_info, validate='key')
        self.input_semester = tk.StringVar(self.frame_left_info)
        self.input_reg_no = tk.Entry(self.frame_left_info)
        self.input_mobile = tk.Entry(self.frame_left_info)
        self.input_blood_group = tk.StringVar(self.frame_left_info)
        self.label_warning = tk.Label(self.frame_left_info)
        self.label_face_cnt = tk.Label(self.frame_left_info, text="Faces in current frame: ")
        self.log_all = tk.Label(self.frame_left_info)

        self.font_title = tkFont.Font(family='Helvetica', size=20, weight='bold')
        self.font_step_title = tkFont.Font(family='Helvetica', size=15, weight='bold')
        self.font_warning = tkFont.Font(family='Helvetica', size=15, weight='bold')

        self.path_photos_from_camera = "data/data_faces_from_camera/"
        self.folder_name=""
        self.current_face_dir = ""
        self.font = cv2.FONT_ITALIC

        # Current frame and face ROI position
        self.current_frame = np.ndarray
        self.face_ROI_image = np.ndarray
        self.face_ROI_width_start = 0
        self.face_ROI_height_start = 0
        self.face_ROI_width = 0
        self.face_ROI_height = 0
        self.ww = 0
        self.hh = 0

        self.out_of_range_flag = False
        self.face_folder_created_flag = False

        # FPS
        self.frame_time = 0
        self.frame_start_time = 0
        self.fps = 0
        self.fps_show = 0
        self.start_time = time.time()

        self.cap = cv2.VideoCapture(0)    # Get video stream from camera

        # self.cap = cv2.VideoCapture("test.mp4")   # Input local video
        
        
    # Mkdir for saving photos and csv
    def pre_work_mkdir(self):
        # Create folders to save face images and csv
        if os.path.isdir(self.path_photos_from_camera):
            pass
        else:
            os.mkdir(self.path_photos_from_camera)
            
        file_path = "data/features_all.csv"
        if not os.path.exists(file_path):
            with open(file_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                # Write the header
                writer.writerow(['Name','Gender','Course','Academic Year','Reg. No','Roll No','Semester','Mobile No','Blood Group'] + [f'Feature_{i}' for i in range(1, 129)])
        else:
            print(f"{file_path} already exists. The file was not created.")


    # Delete old face folders
    def GUI_clear_data(self):
        #  "/data_faces_from_camera/person_x/"...
        folders_rd = os.listdir(self.path_photos_from_camera)
        for i in range(len(folders_rd)):
            shutil.rmtree(self.path_photos_from_camera + folders_rd[i])
        if os.path.isfile("data/features_all.csv"):
            os.remove("data/features_all.csv")
        self.label_cnt_face_in_database['text'] = "0"
        self.existing_faces_cnt = 0
        self.log_all["text"] = "Face images and `features_all.csv` removed!"

    def GUI_get_input_name(self):
        if not self.input_name.get() or not self.validate_roll(self.input_roll.get()):
            # tk.messagebox.showerror('Error', 'Please fill out the form correctly.')
            self.log_all["text"]="Error, Please fill out the form correctly."
            return

    # Set the flag to indicate the form is successfully filled
        self.form_filled = True
        
        self.input_name_char = self.input_name.get()
        self.input_course_char = self.input_course.get()
        self.input_academic_year_char = self.input_academic_year.get()
        self.input_gender_char = self.input_gender.get()
        self.input_reg_no_char = self.input_reg_no.get()
        self.input_roll_char = self.input_roll.get()
        self.input_semester_char = self.input_semester.get()
        self.input_mobile_char = self.input_mobile.get()
        self.input_blood_group_char = self.input_blood_group.get()

        self.create_face_folder()
        self.label_cnt_face_in_database['text'] = str(self.existing_faces_cnt)
        
    def GUI_info(self):
        self.form_filled = False
        tk.Label(self.frame_left_info,
                text="STUDENT REGISTRATION",
                font=("Arial", 24)).grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=2, pady=20)

        tk.Label(self.frame_left_info, text="FPS: ").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.label_fps_info.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        tk.Label(self.frame_left_info, text="Faces in database: ").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.label_cnt_face_in_database.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        tk.Label(self.frame_left_info,
                text="Faces in current frame: ").grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        self.label_face_cnt.grid(row=3, column=2, columnspan=3, sticky=tk.W, padx=5, pady=2)

        self.label_warning.grid(row=4, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)

        # Step 1: Input name and other details, create folders for face
        tk.Label(self.frame_left_info,
                font=("Arial", 18),
                text="Step 2: Student details").grid(row=7, column=0, columnspan=2, sticky=tk.W, padx=5, pady=20)

        tk.Label(self.frame_left_info, text="Name: ").grid(row=8, column=0,columnspan=5, sticky=tk.W, padx=5, pady=0)
        self.input_name.grid(row=8, column=1, sticky=tk.W, padx=0, pady=2)

        tk.Label(self.frame_left_info, text="Gender: ").grid(row=9, column=0, sticky=tk.W, padx=5, pady=0)
        gender_choices = ['Male', 'Female', 'Other']  # Add your gender choices here
        self.input_gender.set(gender_choices[0])  # Set the default value
        tk.OptionMenu(self.frame_left_info, self.input_gender, *gender_choices).grid(row=9, column=1, sticky=tk.W, padx=0, pady=2)

        tk.Label(self.frame_left_info, text="Course: ").grid(row=10, column=0, sticky=tk.W, padx=5, pady=0)
        course_choices = ['B.Tech', 'M.C.A', 'M.Tech']  # Add your course choices here
        self.input_course.set(course_choices[0])  # Set the default value
        tk.OptionMenu(self.frame_left_info, self.input_course, *course_choices).grid(row=10, column=1, sticky=tk.W, padx=0, pady=2)

        tk.Label(self.frame_left_info, text="Academic Year: ").grid(row=11, column=0, sticky=tk.W, padx=5, pady=0)
        academic_year_choices = ['2021-22', '2022-23', '2023-24', '2024-25']  # Add your academic year choices here
        self.input_academic_year.set(academic_year_choices[0])  # Set the default value
        tk.OptionMenu(self.frame_left_info, self.input_academic_year, *academic_year_choices).grid(row=11, column=1, sticky=tk.W, padx=0, pady=2)

        tk.Label(self.frame_left_info, text="Reg. No: ").grid(row=12, column=0, columnspan=5,sticky=tk.W, padx=5, pady=0)
        self.input_reg_no.grid(row=12, column=1, sticky=tk.W, padx=0, pady=2)

        tk.Label(self.frame_left_info, text="Roll No: ").grid(row=13, column=0,columnspan=5, sticky=tk.W, padx=5, pady=0)
        self.input_roll['validatecommand'] = (self.input_roll.register(self.validate_roll), '%P')
        self.input_roll.grid(row=13, column=1, sticky=tk.W, padx=0, pady=2)
        
        tk.Label(self.frame_left_info, text="Semester: ").grid(row=14, column=0, sticky=tk.W, padx=5, pady=0)
        semester_choices = ['1st', '2nd', '3rd', '4th', '5th', '6th']  # Add your semester choices here
        self.input_semester.set(semester_choices[0])  # Set the default value
        tk.OptionMenu(self.frame_left_info, self.input_semester, *semester_choices).grid(row=14, column=1, sticky=tk.W, padx=0, pady=2)

        tk.Label(self.frame_left_info, text="Mobile No: ").grid(row=15, column=0, sticky=tk.W, padx=5, pady=0)
        self.input_mobile.grid(row=15, column=1, sticky=tk.W, padx=0, pady=2)

        tk.Label(self.frame_left_info, text="Blood Group: ").grid(row=16, column=0, sticky=tk.W, padx=5, pady=0)
        blood_group_choices = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']  # Add your blood group choices here
        self.input_blood_group.set(blood_group_choices[0])  # Set the default value
        tk.OptionMenu(self.frame_left_info, self.input_blood_group, *blood_group_choices).grid(row=16, column=1, sticky=tk.W, padx=0, pady=2)

        tk.Button(self.frame_left_info,
                text='Save',
                command=self.GUI_get_input_name).grid(row=17, columnspan=3, padx=5)

        # Step 1: Save current face in frame
        tk.Label(self.frame_left_info,
                font=("Arial", 18),
                text="Click Student Live Images:").grid(row=18, column=0, columnspan=2, sticky=tk.W, padx=5, pady=20)

        tk.Button(self.frame_left_info,
                text='Click',
                command=self.save_current_face).grid(row=19, column=0, columnspan=3, sticky=tk.W)

        # Show log in GUI
        self.log_all.grid(row=20, column=0, columnspan=20, sticky=tk.W, padx=5, pady=20)
        self.frame_left_info.pack(side=tk.LEFT)
        
        tk.Button(self.frame_left_info,
        text='Extract',
        command=self.extract_to_csv).grid(row=21, column=0, columnspan=3, sticky=tk.W)


    def validate_roll(self, value):
        if not value:
            return True
        try:
            int(value)
            # Check if the roll number is unique
            with open("data/features_all.csv", 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if value == row['Roll No']:  # Assuming 'roll' is the header for the roll number column
                        return False  # Roll number is not unique
            return True  # Roll number is unique
        except ValueError:
            return False


    def create_face_folder(self):
        #  Create the folders for saving faces
        self.existing_faces_cnt += 1
        self.folder_name = f"{self.input_name_char}_{self.input_gender_char}_{self.input_course_char}_{self.input_academic_year_char}_{self.input_reg_no_char}_{self.input_roll_char}_{self.input_semester_char}_{self.input_mobile_char}_{self.input_blood_group_char}"
        self.current_face_dir = os.path.join(self.path_photos_from_camera, self.folder_name)
        os.makedirs(self.current_face_dir)
        self.log_all["text"] = "\"" + self.current_face_dir + "/\" created!"
        logging.info("\n%-40s %s", "Create folders:", self.current_face_dir)

        self.ss_cnt = 0  # Clear the cnt of screen shots
        self.face_folder_created_flag = True  # Face folder already created

    def save_current_face(self):
        if self.face_folder_created_flag:
            if self.current_frame_faces_cnt == 1:
                if not self.out_of_range_flag:
                    self.ss_cnt += 1
                    # Create blank image according to the size of face detected
                    self.face_ROI_image = np.zeros((int(self.face_ROI_height * 2), self.face_ROI_width * 2, 3),np.uint8)
                    for ii in range(self.face_ROI_height * 2):
                        for jj in range(self.face_ROI_width * 2):
                            self.face_ROI_image[ii][jj] = self.current_frame[self.face_ROI_height_start - self.hh + ii][
                                self.face_ROI_width_start - self.ww + jj]
                    self.log_all["text"] = "\"" + self.current_face_dir + "/img_face_" + str(
                        self.ss_cnt) + ".jpg\"" + " saved!"
                    self.face_ROI_image = cv2.cvtColor(self.face_ROI_image, cv2.COLOR_BGR2RGB)

                    cv2.imwrite(self.current_face_dir + "/img_face_" + str(self.ss_cnt) + ".jpg", self.face_ROI_image)
                    logging.info("%-40s %s/img_face_%s.jpg", "Save into：",str(self.current_face_dir), str(self.ss_cnt) + ".jpg")
                else:
                    self.log_all["text"] = "Please do not out of range!"
            else:
                self.log_all["text"] = "No face in current frame!"
        else:
            self.log_all["text"] = "Please run step 2!"

    def get_frame(self):
        try:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                frame = cv2.resize(frame, (640, 480))
                return ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except:
            print("Error: No video input!!!")
            

    # Update FPS of Video stream
    def update_fps(self):
        now = time.time()
        #  Refresh fps per second
        if str(self.start_time).split(".")[0] != str(now).split(".")[0]:
            self.fps_show = self.fps
        self.start_time = now
        self.frame_time = now - self.frame_start_time
        self.fps = 1.0 / self.frame_time
        self.frame_start_time = now
        self.label_fps_info["text"] = str(self.fps.__round__(2))

    # Main process of face detection and saving
    def process(self):
        ret, self.current_frame = self.get_frame()
        faces = detector(self.current_frame, 0)
        # Get frame
        if ret:
            self.update_fps()
            self.label_face_cnt["text"] = str(len(faces))
            # Face detected
            if len(faces) != 0:
                # Show the ROI of faces
                for k, d in enumerate(faces):
                    self.face_ROI_width_start = d.left()
                    self.face_ROI_height_start = d.top()
                    # Compute the size of rectangle box
                    self.face_ROI_height = (d.bottom() - d.top())
                    self.face_ROI_width = (d.right() - d.left())
                    self.hh = int(self.face_ROI_height / 2)
                    self.ww = int(self.face_ROI_width / 2)

                    # If the size of ROI > 480x640
                    if (d.right() + self.ww) > 640 or (d.bottom() + self.hh > 480) or (d.left() - self.ww < 0) or (
                            d.top() - self.hh < 0):
                        self.label_warning["text"] = "OUT OF RANGE"
                        self.label_warning['fg'] = 'red'
                        self.out_of_range_flag = True
                        color_rectangle = (255, 0, 0)
                    else:
                        self.out_of_range_flag = False
                        self.label_warning["text"] = ""
                        color_rectangle = (255, 255, 255)
                    self.current_frame = cv2.rectangle(self.current_frame,tuple([d.left() - self.ww, d.top() - self.hh]),tuple([d.right() + self.ww, d.bottom() + self.hh]),color_rectangle, 2)
            self.current_frame_faces_cnt = len(faces)

            # Convert PIL.Image.Image to PIL.Image.PhotoImage
            img_Image = Image.fromarray(self.current_frame)
            img_PhotoImage = ImageTk.PhotoImage(image=img_Image)
            self.label.img_tk = img_PhotoImage
            self.label.configure(image=img_PhotoImage)

        # Refresh frame
        self.win.after(20, self.process)
        
        
    # Return 128D features for single image
    def return_128d_features(self,path_img):
        img_rd = cv2.imread(path_img)
        faces = detector(img_rd, 1)

        logging.info("%-40s %-20s", " Image with faces detected:", path_img)

        # For photos of faces saved, we need to make sure that we can detect faces from the cropped images
        if len(faces) != 0:
            shape = predictor(img_rd, faces[0])
            face_descriptor = face_reco_model.compute_face_descriptor(img_rd, shape)
        else:
            face_descriptor = 0
            logging.warning("no face")
        return face_descriptor

    # Return the mean value of 128D face descriptor for person X
    def return_features_mean_personX(self,path_face_personX):
        features_list_personX = []
        photos_list = os.listdir(path_face_personX)
        if photos_list:
            for i in range(len(photos_list)):
                # Get 128D features for single image of personX
                logging.info("%-40s %-20s", " / Reading image:", path_face_personX + "/" + photos_list[i])
                features_128d = self.return_128d_features(path_face_personX + "/" + photos_list[i])
                # Jump if no face detected from image
                if features_128d == 0:
                    i += 1
                else:
                    features_list_personX.append(features_128d)
        else:
            logging.warning(" Warning: No images in%s/", path_face_personX)

        if features_list_personX:
            features_mean_personX = np.array(features_list_personX, dtype=object).mean(axis=0)
        else:
            features_mean_personX = np.zeros(128, dtype=object, order='C')
        return features_mean_personX
        
    def extract_to_csv(self):
        # logging.basicConfig(level=logging.INFO)
        # Get the order of latest person
        # person_list = os.listdir("data/data_faces_from_camera/")
        # person_list.sort()

        with open("data/features_all.csv", "a") as csvfile:
            writer = csv.writer(csvfile)
            # Write the header

            # for person in person_list:
                # Get the mean/average features of face/personX, it will be a list with a length of 128D
            logging.info("%sperson_%s", self.path_photos_from_camera, self.folder_name)
            features_mean_personX = self.return_features_mean_personX(self.current_face_dir)

            # Extract details from the folder name
            details = self.folder_name.split('_')
            if len(details) >= 8:
                person_name = details[0]
                gender = details[1]
                course = details[2]
                academic_year = details[3]
                reg_no = details[4]
                roll_no = details[5]
                semester=details[6]
                mobile = details[7]
                blood_group = details[8]
            else:
                person_name = details[0] if len(details) > 0 else ''
                gender = details[1] if len(details) > 1 else ''
                course = details[2] if len(details) > 2 else ''
                academic_year = details[3] if len(details) > 3 else ''
                reg_no = details[4] if len(details) > 4 else ''
                roll_no = details[5] if len(details) > 5 else ''
                semester = details[6] if len(details) > 6 else ''
                mobile = details[7] if len(details) > 7 else ''
                blood_group = details[8] if len(details) > 8 else ''

            # Insert details and features into the row
            row = [person_name, gender, course, academic_year, reg_no, roll_no, semester,mobile, blood_group] + features_mean_personX.tolist()
            writer.writerow(row)
            logging.info('\n')
            logging.info("Save all the features of faces registered into: data/features_all.csv")
            


    def run(self):
        self.pre_work_mkdir()
        # self.check_existing_faces_cnt()
        self.GUI_info()
        self.process()
        self.win.mainloop()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    Face_Register_con = Face_Register()
    Face_Register_con.run()
