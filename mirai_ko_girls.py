import sys, os, re, time
from PyQt6 import QtWidgets, QtGui, QtCore, uic
from google import genai
from google.genai import types
from PIL import Image  # Used for converting file paths into API image blocks
import hana_persona
import hana2_persona
import pathlib

if hasattr(sys, '_MEIPASS'):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HANA_KEY = "AIzaSyBzutV8aMMcwk7PzSSNx-_fG2FrrAYHfws"
MEIBI_KEY = "AIzaSyAyZn9k4MfWHngY3v7vTpHeZWwvuEr_3j8"


class AIWorker(QtCore.QThread):
    data_signal = QtCore.pyqtSignal(dict)

    def __init__(self, user_text, h_client, m_client, last_hana, last_meibi, staged_image_path=None, target="both"):
        super().__init__()
        self.user_text = user_text
        self.h_client = h_client
        self.m_client = m_client
        self.last_hana = last_hana
        self.last_meibi = last_meibi
        self.staged_image_path = staged_image_path
        self.target = target

    def generate_persona_response(self, prompt, system_instruction, persona_type):
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_LOW_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
        ]

        if persona_type == "hana":
            active_client = self.h_client
        else:
            active_client = self.m_client

        response = active_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                safety_settings=safety_settings,
                temperature=1.0
            )
        )
        return response.text

    def run(self):
        try:
            h_clean, h_f_num = "", "5"
            m_clean, m_f_num = "", "5"
            h_raw = "N/A - Direct Line"
            m_raw = "N/A - Direct Line"

            # 1. HANA THINKS
            if self.target in ["both", "hana"]:
                hana_context = f"{hana_persona.HANA_PROMPT}\n\n"
                if self.last_meibi:
                    hana_context += f"Meibi previously said: {self.last_meibi}\n\n"
                hana_context += f"User: {self.user_text}"

                hana_contents = [hana_context]

                if self.staged_image_path and os.path.exists(self.staged_image_path):
                    try:
                        pil_img_h = Image.open(self.staged_image_path)
                        hana_contents.append(pil_img_h)
                    except Exception as img_err:
                        print(f"Failed to load image for Hana: {img_err}")

                h_res = self.h_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=hana_contents
                )
                h_raw = h_res.text if (h_res and hasattr(h_res, 'text') and h_res.text) else "EMPTY_OR_BLOCKED_RESPONSE"

                if h_raw == "EMPTY_OR_BLOCKED_RESPONSE":
                    h_clean = "An anomaly has occurred. (Request blocked)"
                    h_f_num = "5"
                else:
                    h_clean = re.sub(r"\[FACE:\d+\]", "", h_raw).strip()
                    h_f_match = re.search(r"\[FACE:(\d+)\]", h_raw)
                    h_f_num = h_f_match.group(1) if h_f_match else "5"

                if self.target == "both":
                    time.sleep(0.5)

            # 2. MEIBI THINKS
            if self.target in ["both", "meibi"]:
                current_hana_speech = h_clean if h_clean else self.last_hana

                meibi_context = f"{hana2_persona.HANA2_PROMPT}\n\n"
                if current_hana_speech:
                    meibi_context += f"Hana said: {current_hana_speech}\n\n"
                meibi_context += f"User: {self.user_text}"

                meibi_contents = [meibi_context]

                if self.staged_image_path and os.path.exists(self.staged_image_path):
                    try:
                        pil_img_m = Image.open(self.staged_image_path)
                        meibi_contents.append(pil_img_m)
                    except Exception as img_err:
                        print(f"Failed to load image for Meibi: {img_err}")

                m_res = self.m_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=meibi_contents
                )
                m_raw = m_res.text if (m_res and hasattr(m_res, 'text') and m_res.text) else "EMPTY_OR_BLOCKED_RESPONSE"

                if m_raw == "EMPTY_OR_BLOCKED_RESPONSE":
                    m_clean = "Wait, what happened? (I drifted off...)"
                    m_f_num = "5"
                else:
                    m_clean = re.sub(r"\[FACE:\d+\]", "", m_raw).strip()
                    m_f_match = re.search(r"\[FACE:(\d+)\]", m_raw)
                    m_f_num = m_f_match.group(1) if m_f_match else "5"

            # Forward the data payload back to the UI layout
            self.data_signal.emit({
                "target": self.target,
                "h_t": h_clean,
                "h_f": h_f_num,
                "h_raw_debug": h_raw,
                "m_t": m_clean,
                "m_f": m_f_num,
                "m_raw_debug": m_raw
            })

        except Exception as e:
            print(f"Worker Error: {e}")

Ui_MainWindow, QtBaseClass = uic.loadUiType("Mirai-Ko-Girls-UI.ui")

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # 3. Change uic.loadUi(..., self) to this native setup method:
        self.setupUi(self)

        BASE_DIR = pathlib.Path(__file__).parent.absolute()
        UI_PATH = str(BASE_DIR / "Mirai-Ko-Girls-UI.ui")

        # Quick print to see if Python can physically touch the file
        if not os.path.exists(UI_PATH):
            print(f"\n[ALERT] Python sees the folder but cannot access the file at: {UI_PATH}")
        else:
            print(f"\n[SUCCESS] UI file found and accessed at: {UI_PATH}")

        Ui_MainWindow, QtBaseClass = uic.loadUiType(UI_PATH)

        if os.path.exists("mirai_logo.ico"):
            self.setWindowTitle("Mirai-Ko Girls")
            self.setWindowIcon(QtGui.QIcon("mirai_logo.ico"))

        self.h_client = genai.Client(api_key=HANA_KEY)
        self.m_client = genai.Client(api_key=MEIBI_KEY)

        self.staged_image_path = None

        # Memory Tracking Registers
        self.last_hana_response = ""
        self.last_meibi_response = ""

        # Connect inputs to execution routing
        self.GlobalChat.returnPressed.connect(lambda: self.start_process("both"))
        self.HanaChatInput.returnPressed.connect(lambda: self.start_process("hana"))
        self.MeibiChatInput.returnPressed.connect(lambda: self.start_process("meibi"))

        self.UploadBtn.clicked.connect(self.select_image)

    def select_image(self):
        file_filter = "Images (*.png *.jpg *.jpeg *.webp)"
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Stage Workspace Image Asset", "", file_filter)
        if file_path:
            self.staged_image_path = file_path
            pix = QtGui.QPixmap(file_path)
            self.ImagePreview.setPixmap(pix.scaled(200, 150, QtCore.Qt.AspectRatioMode.KeepAspectRatio))
            self.hana_log.append("<i>[System: Image asset attached to buffer]</i>")
            self.meibi_log.append("<i>[System: Image asset attached to buffer]</i>")

    def start_process(self, target):
        if target == "both":
            active_box = self.GlobalChat
        elif target == "hana":
            active_box = self.HanaChatInput
        else:
            active_box = self.MeibiChatInput

        self.current_msg = active_box.text().strip()

        if not self.current_msg and not self.staged_image_path:
            return

        active_box.clear()

        # Lock down inputs to prevent race conditions
        self.GlobalChat.setEnabled(False)
        self.HanaChatInput.setEnabled(False)
        self.MeibiChatInput.setEnabled(False)

        if self.current_msg:
            user_line = f"<b>You:</b> {self.current_msg}"
        else:
            user_line = f"<b>You:</b> <i>[Sent an Image Asset]</i>"

        if target in ["both", "hana"]:
            self.hana_log.append(user_line)
        if target in ["both", "meibi"]:
            self.meibi_log.append(user_line)

        self.worker = AIWorker(
            self.current_msg,
            self.h_client,
            self.m_client,
            self.last_hana_response,
            self.last_meibi_response,
            self.staged_image_path,
            target
        )
        self.worker.data_signal.connect(self.update_ui, QtCore.Qt.ConnectionType.QueuedConnection)
        self.worker.start()

    def update_ui(self, data):
        print(f"\n--- RAW HANA ANSWER ---\n{data['h_raw_debug']}\n------------------------")
        print(f"--- RAW MEIBI ANSWER ---\n{data['m_raw_debug']}\n------------------------\n")

        target = data['target']

        # Update Hana layout if targeted
        if target in ["both", "hana"]:
            self.hana_log.append(f"<span style='color:cyan;'>Hana:</span> {data['h_t']}")
            self.draw_face("hana", data['h_f'])
            if data['h_t'] and data['h_t'] != "An anomaly has occurred. (Request blocked)":
                self.last_hana_response = data['h_t']

        # FIX: Changed target check from "hana2" to "meibi" so the logs actually update!
        if target in ["both", "meibi"]:
            self.meibi_log.append(f"<span style='color:yellow;'>Hana:</span> {data['m_t']}")
            self.draw_face("meibi", data['m_f'])
            if data['m_t'] and data['m_t'] != "An anomaly has occurred. (Request blocked)":
                self.last_meibi_response = data['m_t']

        # Clean workspace staging asset buffers
        self.staged_image_path = None
        if hasattr(self, 'ImagePreview'):
            self.ImagePreview.clear()

        # Unlock line inputs
        self.GlobalChat.setEnabled(True)
        self.HanaChatInput.setEnabled(True)
        self.MeibiChatInput.setEnabled(True)

        if target == "hana":
            QtCore.QTimer.singleShot(100, lambda: self.HanaChatInput.setFocus())
        elif target == "meibi":
            QtCore.QTimer.singleShot(100, lambda: self.MeibiChatInput.setFocus())
        else:
            QtCore.QTimer.singleShot(100, lambda: self.GlobalChat.setFocus())

    def draw_face(self, girl, num):
        # Translate the background folder name for your mod
        folder_name = "hana2_faces" if girl.lower() == "meibi" else f"{girl.lower()}_faces"

        path = os.path.join("assets", folder_name, f"{num}.png")
        if os.path.exists(path):
            pix = QtGui.QPixmap(path)
            if girl == "hana":
                if hasattr(self, 'Face'):
                    self.Face.setPixmap(pix)
                else:
                    print("Warning: 'Face' object not found in UI layout.")
            else:
                # Safe check if Face_2 exists, or look for it if it was renamed
                if hasattr(self, 'Face_2'):
                    self.Face_2.setPixmap(pix)
                elif hasattr(self, 'Face_1'):
                    self.Face_1.setPixmap(pix)
                else:
                    print(f"Warning: Could not find image label for {girl}'s 3D face in the UI layout.")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())