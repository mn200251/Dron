
# **DIY Drone with Android App and Python Server**

The project is a comprehensive system designed to enable real-time drone control via a custom Android mobile application. This project integrates various components, including an Android app, a Python server, and a DIY drone equipped with a Raspberry Pi 5 for processing and control. The system allows users to control the drone, stream video feed, manage recordings, and automate tasks through macro commands.

The focus of the project is on seamless interaction between the user and the drone, enabling intuitive control, real-time data processing, and efficient video management. A core part of the project involves overcoming the technical challenges of drone flight stabilization, reliable data communication, and real-time control.


## **Features**

The project brings a host of advanced features that are designed to provide users with intuitive control over their drone, alongside real-time data streaming and processing capabilities. Key features include:

- **Real-Time Control**: The Android app allows users to control the drone's movement using virtual joysticks. The control is smooth, precise, and intuitive, providing an experience similar to professional drone controllers.

- **Live Video Streaming**: Users can view real-time video feeds from the drone’s onboard camera directly on the app. The video is compressed and transmitted using OpenCV and displayed in the app for seamless first-person viewing (FPV).

- **Macro Command System**: The app allows for recording a series of control commands (macros) that can be replayed to automate specific tasks. This feature makes repetitive flight maneuvers simple to execute without constant manual input.

- **Video Recording and Management**: The app can record videos captured by the drone during flight. Users can then manage, download, rename, and delete these recordings through an integrated video management interface.


## **Installation**

Install my-project with npm

```bash
  npm install my-project
  cd my-project
```
    
## **Tech Stack**

### **Drone**

The drone is powered by a Raspberry Pi and a set of hardware components that work in tandem to ensure flight stability and responsiveness. The tech stack for the drone includes the following:

- **Raspberry Pi 5**: Acts as the central processing unit (CPU) for the drone, running the software responsible for processing sensor data and controlling the motors. The Raspberry Pi 5 offers increased computational power, allowing for advanced processing capabilities compared to traditional flight controllers.

- **MPU6050 Sensor**: This sensor provides the drone with real-time orientation data by measuring acceleration (accelerometer) and angular velocity (gyroscope) in three axes. The data collected by the sensor is critical for maintaining stability and balance during flight.

- **PCA9685 PWM Module**: The PCA9685 module generates the Pulse Width Modulation (PWM) signals needed to control the speed of the drone's motors. This is particularly important for maintaining stable flight, as each motor needs to be precisely controlled.

- **Python 3.12**: Python is used as the primary programming language for the drone’s control software. Its extensive library support and ease of hardware integration make it a great choice for real-time control applications.

- **NumPy**: Used extensively for performing mathematical computations necessary for the flight control system. NumPy processes data from the sensors, calculates the necessary motor adjustments, and feeds this information to the Raspberry Pi.

- **OpenCV**: This powerful computer vision library captures video frames from the drone’s onboard camera, which are compressed and sent to the server. It also allows for potential future enhancements, such as object detection.

- **smbus2**: This library enables I2C communication between the Raspberry Pi and the other hardware components, such as the MPU6050 sensor and PCA9685 PWM module, ensuring smooth and reliable data exchange.


### **Android Application**
The Android app serves as the main interface for users to interact with the drone, providing real-time control, video streaming, and telemetry data. It was developed using modern tools and libraries to ensure responsiveness, reliability, and ease of use. The tech stack for the Android app includes:

- **Android Studio (Koala)**: The app was developed in the Android Studio environment, specifically the "Koala" version, which offers enhanced tooling for Kotlin development and Compose UI building.

- **Kotlin**: The programming language used to build the Android app. Kotlin offers a modern syntax, improved performance over Java, and seamless integration with Jetpack Compose and Android libraries, making it ideal for developing interactive mobile applications.

- **Jetpack Compose**: This is the backbone of the user interface, enabling declarative UI development. Using Compose allows for building responsive, scalable UIs with fewer lines of code. The following Jetpack Compose dependencies are included:

    - `androidx.compose.ui` for core UI elements.
    - `androidx.compose.ui-graphics` for rendering graphics.
    - `androidx.compose.material3` for creating modern, material design components.
    - `androidx.compose.ui-tooling` for previewing UI directly in the Android Studio IDE.

- **Lifecycle KTX (**`androidx.lifecycle`**)**: The lifecycle-runtime-ktx and lifecycle-viewmodel-ktx libraries manage the lifecycle of UI components. These are used to manage state and data persistence during the app's lifecycle, ensuring efficient resource management and state consistency even with activity restarts or configuration changes.

- **Material3**: This library is used to provide a consistent and modern user interface design, adhering to the latest Material Design guidelines. It offers pre-built components such as buttons, sliders, and text fields, which are extensively used in the app’s control screens.

- **GitHub API**: The app uses the GitHub API to fetch the current server IP address from a private GitHub repository. This allows the app to always connect to the latest server instance dynamically.

- **Kotlinx Serialization**: This library is used for encoding and decoding data into JSON format, making it easier to send and receive structured data between the Android app and the server.

- **Core-KTX (**`androidx.core`**)**: This library provides Kotlin-friendly extensions for Android’s core APIs, making it easier to work with fundamental Android features like SharedPreferences, notifications, and resource handling.
### **Server**

The server plays a crucial role in relaying information between the Android app and the drone. It processes incoming commands, sends responses, and manages video streaming in real time. The server is designed for high efficiency and concurrency, though future improvements in architecture are planned. The tech stack for the server includes:

- **Python 3.12**: The server is built using Python, a powerful language known for its simplicity and versatility. Python’s extensive library support and its ease of development make it ideal for rapid prototyping and building the middleware for drone control.

- **Multiprocessing Library**: To handle multiple incoming requests (from the app and drone) simultaneously, the server leverages Python’s multiprocessing library. This allows the server to create multiple processes that can handle video processing and command execution without blocking.

- **Threading**: In addition to multiprocessing, the server uses threading to handle multiple simultaneous connections from the drone and Android app. The threading library ensures that the server can respond quickly to different requests, like controlling the drone, processing commands, and sending video data back to the app.

- **Socket**: The socket library is crucial for setting up the communication pipelines between the server, drone, and Android app. It establishes TCP sockets for the real-time transmission of data, ensuring robust communication even in unstable network conditions.

- **Queue**: The server uses a queue to manage incoming and outgoing commands, ensuring that instructions are processed in the correct order. This helps in maintaining consistency between the app and the drone’s operations.

- **os**: The os module plays a key role in saving videos, macro commands, renaming and deleting from server storage.

- **OpenCV**: On the server side, OpenCV is used to process and compress video frames sent from the drone. It ensures that the video stream is efficiently transferred to the Android app without causing excessive network load or latency issues.

- **PyGitHub**: The server dynamically updates its IP address in a private GitHub repository whenever it changes, ensuring that the Android app and the drone can always connect to the latest server address without requiring manual intervention.

- **TCP Protocol**: The server relies on the TCP protocol to ensure reliable communication between the Android app and the drone. While TCP offers strong error correction and data integrity, future enhancements may explore using UDP for faster video transmission.