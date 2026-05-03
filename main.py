

import streamlit as st
import cv2
import os
import json
import numpy as np
import serial
import time
from datetime import datetime
import pandas as pd

# -------------------------
# App Config
# -------------------------
st.set_page_config(page_title="Face + Password Auth", layout="centered")

# -------------------------
# Admin Password (Change this!)
# -------------------------
ADMIN_PASSWORD = "admin123"  # Change this to your secure password

# -------------------------
# Helpers
# -------------------------
def open_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 15)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    return cap

def send_signal(signal):
    try:
        arduino = serial.Serial('COM3', 9600, timeout=1)
        time.sleep(2)
        arduino.write(signal.encode())
        arduino.close()
    except:
        st.warning("⚠️ Arduino not connected")

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

def save_logs():
    with open("logs.json", "w") as f:
        json.dump(logs, f, indent=4)

def add_log(username, status):
    logs.append({
        "user": username,
        "status": status,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_logs()

def delete_user(username):
    if username in users:
        # Delete face images
        if os.path.exists("dataset"):
            for file in os.listdir("dataset"):
                if file.startswith(username):
                    os.remove(os.path.join("dataset", file))
        # Delete from users
        del users[username]
        save_users()
        # Retrain model
        train_model()
        return True
    return False

# -------------------------
# Load Data
# -------------------------
if os.path.exists("users.json"):
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        users = {}
else:
    users = {}

if os.path.exists("logs.json"):
    try:
        with open("logs.json", "r") as f:
            logs = json.load(f)
    except:
        logs = []
else:
    logs = []

# -------------------------
# Face Detectors
# -------------------------
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
profile_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")

# -------------------------
# Train Model
# -------------------------
def train_model():
    if not os.path.exists("dataset"):
        return False

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faces, ids = [], []

    usernames = list(users.keys())

    for file in os.listdir("dataset"):
        path = os.path.join("dataset", file)
        try:
            img = cv2.imread(path, 0)
            if img is None:
                continue
            username = file.split(".")[0]
            if username in usernames:
                idx = usernames.index(username)
                faces.append(img)
                ids.append(idx)
        except:
            continue

    if len(faces) == 0:
        return False

    recognizer.train(faces, np.array(ids))
    recognizer.save("trainer.yml")
    return True

# -------------------------
# Face Login
# -------------------------
def face_login_streamlit(username):
    if not os.path.exists("trainer.yml"):
        st.error("⚠️ No trained model found. Please register first.")
        return None, "NoModel"

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("trainer.yml")

    cap = open_camera()
    if not cap.isOpened():
        st.error("Camera not accessible")
        return None, "CameraError"

    for _ in range(5):
        cap.read()

    FRAME_WINDOW = st.image([])
    confidence_threshold = 60
    consecutive_matches = 0
    result_user = None

    st.info("📸 Looking for face match... Stay in frame!")

    for _ in range(120):
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.2, 4, minSize=(60, 60))
        if len(faces) == 0:
            faces = profile_detector.detectMultiScale(gray, 1.2, 4, minSize=(60, 60))

        label = "No face"
        color = (0, 165, 255)

        for (x, y, w, h) in faces:
            roi = gray[y:y+h, x:x+w]
            if roi.size == 0:
                continue

            roi = cv2.resize(roi, (200, 200))
            predicted_id, conf = recognizer.predict(roi)

            usernames = list(users.keys())
            predicted_user = usernames[predicted_id] if predicted_id < len(usernames) else "Unknown"

            if conf < confidence_threshold and predicted_user == username:
                consecutive_matches += 1
                label = f"✅ MATCH: {predicted_user} ({int(conf)})"
                color = (0, 255, 0)
                if consecutive_matches >= 3:
                    result_user = username
            else:
                consecutive_matches = 0
                label = f"❌ {predicted_user} ({int(conf)})" if conf < confidence_threshold else f"Unknown ({int(conf)})"
                color = (0, 0, 255) if conf < confidence_threshold else (0, 165, 255)

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, max(25, y-10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            break

        FRAME_WINDOW.image(frame, channels="BGR")

        if result_user:
            break

        time.sleep(0.01)

    cap.release()
    return result_user, "Authorized" if result_user else "FaceMismatch"

# -------------------------
# UI
# -------------------------
st.title("🔐 Face Recognition & Password Authentication System")

menu = ["Login", "Register", "Logs", "🔧 Admin Panel"]
choice = st.sidebar.selectbox("Choose Option", menu)

# -------------------------
# Register
# -------------------------
if choice == "Register":
    st.subheader("👤 Register New User")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        if username in users:
            st.error("❌ User already exists!")
        elif username == "" or password == "":
            st.warning("⚠️ Please fill all fields")
        else:
            os.makedirs("dataset", exist_ok=True)
            cam = open_camera()

            if not cam.isOpened():
                st.error("Camera not accessible!")
            else:
                for _ in range(5):
                    cam.read()

                count = 0
                FRAME_WINDOW = st.image([])
                progress = st.progress(0)
                st.info("📸 Capturing 25 face samples... Keep face centered!")

                while count < 25:
                    ret, img = cam.read()
                    if not ret:
                        break

                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = face_detector.detectMultiScale(gray, 1.2, 4, minSize=(80, 80))

                    for (x, y, w, h) in faces:
                        face_roi = gray[y:y+h, x:x+w]
                        if face_roi.size == 0:
                            continue

                        face_roi = cv2.resize(face_roi, (200, 200))
                        cv2.imwrite(f"dataset/{username}.{count+1}.jpg", face_roi)

                        count += 1
                        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(img, f"Captured: {count}/25", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        break

                    FRAME_WINDOW.image(img, channels="BGR")
                    progress.progress(count / 25)
                    time.sleep(0.03)

                cam.release()

                users[username] = {"password": password}
                save_users()

                if train_model():
                    st.success("✅ Registered & Trained Successfully!")
                else:
                    st.error("❌ Training failed. Check dataset.")

# -------------------------
# Login
# -------------------------
elif choice == "Login":
    st.subheader("🔐 Dual Authentication (Password → Face)")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("OPEN GATE (Password + Face)"):
            if username in users and users[username]["password"] == password:
                st.success("✅ Password Verified!")
                st.info("🎥 Now verifying face...")

                with st.spinner("Scanning face..."):
                    user, status = face_login_streamlit(username)

                if user:
                    st.success(f"🎉 Fully Authorized: {user} ✅")
                    send_signal('OPEN\n')
                    add_log(user, "Authorized (Password+Face)")
                else:
                    st.error("❌ Face mismatch!")
                    send_signal('CLOSE\n')
                    add_log(username, "Face Mismatch")
            else:
                st.error("❌ Wrong credentials!")
                send_signal('CLOSE\n')
                add_log(username, "Wrong Password")

# -------------------------
# Logs
# -------------------------
elif choice == "Logs":
    st.subheader("📋 Access Logs")

    if logs:
        df = pd.DataFrame(logs[-50:][::-1])
        st.dataframe(df, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            total = len(logs)
            st.metric("Total Attempts", total)
        with col2:
            success = len([l for l in logs if "Authorized" in l["status"]])
            st.metric("Success Rate", f"{success}/{total} ({success/total*100:.1f}%)")
        with col3:
            st.download_button("📥 Download Logs", 
                             data=json.dumps(logs, indent=2),
                             file_name=f"access_logs_{datetime.now().strftime('%Y%m%d')}.json")
    else:
        st.info("📭 No logs yet")

# -------------------------
# Admin Panel
# -------------------------
elif choice == "🔧 Admin Panel":
    st.subheader("🔧 Admin Control Panel")
    
    admin_password = st.text_input("🔑 Admin Password", type="password")
    
    if admin_password == ADMIN_PASSWORD:
        st.success("✅ Admin Access Granted!")
        # st.balloons()  # Balloon animation disabled
        
        tab1, tab2, tab3 = st.tabs(["👥 Users & Logs", "📊 Analytics", "⚙️ System"])
        
        with tab1:
            st.markdown("### 👤 User Management")
            if users:
                for username in list(users.keys()):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"👤 **{username}**")
                    with col2:
                        if st.button("🗑️ Delete", key=f"del_{username}"):
                            if delete_user(username):
                                st.success(f"✅ {username} deleted!")
                                st.rerun()
                            else:
                                st.error("❌ Delete failed!")
            else:
                st.info("📭 No users registered")
            
            st.markdown("---")
            
            st.markdown("### 📋 Logs Management")
            col_logs1, col_logs2 = st.columns(2)
            
            with col_logs1:
                if st.button("🗑️ Clear All Logs", type="secondary"):
                    logs.clear()
                    save_logs()
                    st.success("✅ All logs cleared!")
                    st.rerun()
            
            with col_logs2:
                if logs:
                    log_count = st.number_input("Delete last N logs", min_value=1, max_value=len(logs), value=min(10, len(logs)))
                    if st.button(f"🗑️ Last {log_count}", type="secondary"):
                        logs[:] = logs[:-log_count]
                        save_logs()
                        st.success(f"✅ {log_count} logs deleted!")
                        st.rerun()
                else:
                    st.info("📭 No logs")
            
            st.markdown("---")
            
            if st.button("💥 Full System Reset", type="primary"):
                if st.button("⚠️ CONFIRM FULL RESET", type="primary"):
                    if os.path.exists("dataset"):
                        for file in os.listdir("dataset"):
                            os.remove(os.path.join("dataset", file))
                    users.clear()
                    logs.clear()
                    if os.path.exists("trainer.yml"):
                        os.remove("trainer.yml")
                    save_users()
                    save_logs()
                    st.success("✅ System fully reset!")
                    st.rerun()
        
        with tab2:
            st.subheader("📊 Advanced Logs Analytics")
            
            if logs:
                df = pd.DataFrame(logs)
                
                col1, col2 = st.columns(2)
                with col1:
                    status_filter = st.multiselect("Filter Status", 
                                                 ["Authorized", "Face Mismatch", "Wrong Password"],
                                                 default=["Authorized", "Face Mismatch", "Wrong Password"])
                with col2:
                    days = st.slider("Last N Days", 1, 30, 7)
                
                st.dataframe(df.tail(100), use_container_width=True)
                
                st.subheader("📈 Charts")
                fig_col1, fig_col2 = st.columns(2)
                
                with fig_col1:
                    status_counts = df['status'].value_counts()
                    st.bar_chart(status_counts)
                
                with fig_col2:
                    df_time = pd.DataFrame(logs)
                    df_time['time'] = pd.to_datetime(df_time['time'])
                    hourly = df_time.groupby(df_time['time'].dt.hour).size()
                    st.line_chart(hourly)
                
                st.download_button("📥 Export CSV", 
                                 data=df.to_csv(index=False),
                                 file_name=f"admin_logs_{datetime.now().strftime('%Y%m%d')}.csv")
            else:
                st.info("📭 No logs available")
        
        with tab3:
            st.subheader("⚙️ System Status")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Users", len(users))
            with col2:
                st.metric("Total Logs", len(logs))
            with col3:
                model_status = "✅ Ready" if os.path.exists("trainer.yml") else "❌ Train Needed"
                st.metric("Model Status", model_status)
            
            if st.button("🔄 Retrain All Models"):
                if train_model():
                    st.success("✅ All models retrained!")
                else:
                    st.error("❌ Training failed!")
            

    
    else:
        st.info("This section is for administrators only. Please enter the correct password to access admin features.")

       
