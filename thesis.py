from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from imutils import face_utils
import imutils
import dlib
import cv2
import numpy as np
from matplotlib.path import Path
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from kivy.uix.popup import Popup
from kivy.uix.label import Label


detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

const_max_a_eyes = 7.245
const_max_b_eyes = 1.0001
const_min_a_lips = 12.984
const_min_eyes = 0.071
const_max_eyes = 0.958


class MyWidget(BoxLayout):

    def selected(self, filename):
        try:
            detection(filename[0])
        except:
            show_popup("Something went wrong")


class ThesisApp(App):
    def build(self):
        return MyWidget()


def detection(link):
    try:
        image = cv2.imread(link)
        image = imutils.resize(image, width=500)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except:
        show_popup("Invalid file")

    else:
        # detect faces in the grayscale image
        rects = detector(gray, 1)
        if len(rects) == 0:
            show_popup("No face detected")
        else:
            for (i, rect) in enumerate(rects):
                # determine the facial landmarks for the face region, then
                # convert the landmark (x, y)-coordinates to a NumPy array
                shape = predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)

                enough = 0
                # loop over the face parts individually
                for (name, (i, j)) in face_utils.FACIAL_LANDMARKS_IDXS.items():
                    img = crop_image(shape[i:j], link)
                    if name == 'mouth':
                        a_lip, sum_lip = calculate_a_sum(img)
                        enough += 1
                    if name == 'inner_mouth':
                        a_inner, sum_inner = calculate_a_sum(img)
                        a_lip -= a_inner
                        sum_lip -= sum_inner
                    if name == 'right_eye':
                        a_right_eye, b_right_eye, sum_right_eye = calculate_a_b_sum(img)
                        enough += 1
                    if name == 'left_eye':
                        a_left_eye, b_left_eye, sum_left_eye = calculate_a_b_sum(img)
                        enough += 1

            if enough < 3:
                show_popup("Not enough facial landmarks detected")
            else:
                a_sum_eye = (a_left_eye + a_right_eye) / ((sum_left_eye + sum_right_eye))
                b_sum_eye = (b_left_eye + b_right_eye) / (sum_left_eye + sum_right_eye)
                a_sum_lip = a_lip / sum_lip
                eyes = sum_left_eye / sum_right_eye
                text = "List of possible diseases:\n"
                if a_sum_eye > const_max_a_eyes:
                    text += "Scleritis\nSubconjunctival Hemorrhage\nCorneal Ulcer\nExtraocular Muscle Entrapment (Inf Rectus)" \
                            "\nMuddy Brown Sclera\nPeriorbital Cellulitis\nPeriorbital Echymosis"
                if b_sum_eye > const_max_b_eyes:
                    text += "\nIcterus"
                if a_sum_lip > const_min_a_lips:
                    text += "\nCyanosis"
                if eyes > const_min_eyes + const_max_eyes or eyes < const_max_eyes - const_min_eyes:
                    text += "\nCentral CN 7 Palsy\nPeripheral CN7 Palsy\nExtraocular Muscle Entrapment (Inf Rectus)\nHorner’s Syndrome" \
                            "\nPeriorbital Cellulitis\nPeriorbital Echymosis"
                if text == "List of possible diseases:\n":
                    show_popup("No symptoms detected")
                else:
                    show_popup(text)


def calculate_a_sum(photo):
    a = []
    for i in range(photo.shape[0]):
        for j in range(photo.shape[1]):
            pixel = photo[i][j]
            a1, a2, a3 = pixel / 255
            rgb = sRGBColor(a1, a2, a3)
            if rgb.rgb_r != 0 or rgb.rgb_g != 0 or rgb.rgb_b != 0:
                a.append(rgb_to_cielab(pixel).lab_a)

    av_a = sum(a)
    return av_a, len(a)


def calculate_a_b_sum(photo):
    a = []
    b = []
    for i in range(photo.shape[0]):
        for j in range(photo.shape[1]):
            pixel = photo[i][j]
            a1, a2, a3 = pixel / 255
            rgb = sRGBColor(a1, a2, a3)
            if rgb.rgb_r != 0 or rgb.rgb_g != 0 or rgb.rgb_b != 0:
                a.append(rgb_to_cielab(pixel).lab_a)
                b.append(rgb_to_cielab(pixel).lab_b)

    av_a = sum(a)
    av_b = sum(b)

    return av_a, av_b, len(a)


def rgb_to_cielab(a):
    # a is a pixel with RGB coloring
    a1,a2,a3 = a/255

    color1_rgb = sRGBColor(a1, a2, a3)

    color1_lab = convert_color(color1_rgb, LabColor)

    return color1_lab


def crop_image(part, link):
    vertices = part

    image = cv2.imread(link)
    img = imutils.resize(image, width=500)

    # from vertices to a matplotlib path
    path = Path(vertices)

    # create a mesh grid for the whole image, you could also limit the
    # grid to the extents above, I'm creating a full grid for the plot below
    x, y = np.mgrid[:img.shape[1], :img.shape[0]]
    # mesh grid to a list of points
    points = np.vstack((x.ravel(), y.ravel())).T

    # select points included in the path
    mask = path.contains_points(points)

    # reshape mask for display
    img_mask = mask.reshape(x.shape).T

    # masked image
    img *= img_mask[..., None]
    return img


def show_popup(output):
    popupWindow = Popup(title="Medical Diagnostic", content=Label(text=output), size_hint=(None, None), size=(400, 400))
    popupWindow.open()


if __name__ == '__main__':
    ThesisApp().run()