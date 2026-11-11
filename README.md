
# Neato D.A.W.G
**Avani Patil, Trevor McDonald, Vanessa Flores**  
CompRobo 2026, Machine Vision Project

## Overview
The Neato Dynamic Autonomous Walker with Gestures (D.A.W.G) is an obedient neato that follows three basic commands from any user. Using Mediapipe, the neato D.A.W.G. is trained to recognize hand signals that correlate to movements. The following gestures and their respective movements are:
* Open hand - The D.A.W.G "sits" by moving backwards $\sim 0.8\text{ meters}$ before coming to a stop.
* Hand cupped into a circle - This D.A.W.G. completes one full revolution before coming to a stop.
* Peace sign - The D.A.W.G "fetches." It has been trained using a custom YOLO dataset to recognize a red expo marker and grab it. It first spins in a circle to search for the red expo marker. Once it locates one, it steers in the direction of the marker to "pick it up." It then spins in place until a new command is given.

## Architecture Overview
Our project implements a control node, gesture node, and three behavioral nodes: spin, sit, and fetch. Below is a diagram of our finite state machine showcasing how these nodes interact with each other.

![Finite state machine diagram](neato_dog/images/Screenshot%20from%202026-11-10%2020-59-09.png)

Our D.A.W.G.'s initial state is set to idle. From there, it can process three hand gestures and perform the three commands outlined above. If a new command is given while it is in the process of executing another command, it will run the new command given. Once it completes the command, it returns to the idle state. Notably, the fetch behavior doesn't return to its idle state. If it is fetching and it is unable to find an object, it will continue searching until it finds one, or a new command is given.

## Gesture Detection
To determine which behavior to exhibit, the D.A.W.G gets input from hand gestures. To classify hand gestures, the MediaPipe library is used. The MediaPipe library identifies points on the user's hands. The positions of these points are used to determine what hand gesture is being shown to the neato's camera. The three gestures that are recognized are an open hand, a zero sign, and a peace sign. The gesture node subscribes to the neato camera and dictates which gesture has been detected for the states to switch.

## MediaPipe
MediaPipe has 20 predetermined landmark points that are recognized on a hand.

![MediaPipe diagram](neato_dog/images/Screenshot%20from%202026-11-10%2020-46-33.png)

### Open Hand
For the open hand gesture, the y position of finger tip points 8, 12, 16, and 20 have to be above the finger pip points of 6, 10, 14, 18. 

![open hand diagram](neato_dog/images/Screenshot%20from%202026-11-10%2020-40-11.png)

### Zero
For the zero hand gesture, the difference from the middle finger tip to the thumb tip was determined. If the difference is less than $0.07$ of the image's height, a zero is recognized.

![zero diagram](neato_dog/images/Screenshot%20from%202026-11-10%2020-48-00.png)

### Peace Sign

For the peace sign gesture, the finger tip landmarks corresponding to the pointer and middle fingers (8 and 12) were taken and compared to be above the y of the same fingers' pip landmarks (6 and 10). The finger tip landmarks of the ring and pinky fingers (16 and 20) were taken and compared to be below their corresponding finger pips (14 and 18).

![peace diagram](neato_dog/images/Screenshot%20from%202026-11-10%2020-57-58.png)


Once the gestures were implemented and tested, a gesture node was created to subscribe to the neato's camera. The ROS image is taken and converted into an OpenCV image using cv_bridge. The image is converted from BGR to RGB, since MediaPipe expects RGB input, and passed to MediaPipe to find the hand landmarks. These landmarks are then passed to classify_hand_gestures in a hand_gestures, which returns which gesture was detected. The gesture node also acts as the controller for the D.A.W.G's behaviors. It creates the sit, spin, and fetch behavior nodes and switches between them based on the detected gesture. All four nodes are run together using a Multi Threaded Executor which lets each node's callbacks run at the same time instead of waiting on each other.

## Sit
When performing the sit behavior, the neato halts, backs away from the human, and halts again. The main loop is time based, with the halts lasting 0.5 seconds and backwards movement lasting 2 seconds at a velocity of $0.3\text{ m/s}$. These motions are set as steps (halt being step 0 and backwards movement being step 1) that occur once their respective time limits have passed. Once the behavior is completed, the neato returns to its idle state. Because this loop is not odometry based, we are unable to receive encoder feedback and ensure the neato is hitting the roughly 0.8 meter translation each time. Though this method does not affect the system's main functionality, it would be best to modify the current script to rely on odometry rather than time for more precision.

## Spin
This behavior relies on encoder data to ensure the neato performs the full 360 spin. This node is subscribed to the odometry topic and uses the tf_transformations library to convert the raw quaternion data into heading angles. The main loop begins by capturing the initial heading. As the neato spins, the script calculates the small incremental change in angle from the current position to the last captured position. This change value is then added to the cumulative total angle turned counter. While the total angle is less than $2\pi$ radians, the neato will continue to receive angular velocity commands of $0.7\text{ m/s}$ to spin in place.

```python
# Calculate angle turned non-blockingly
self.total_turned += math.atan2(math.sin(self.yaw - self.start_yaw), math.cos(self.yaw - self.start_yaw))
self.start_yaw = self.yaw
```

```python
if self.total_turned < 2 * math.pi:
    # Keep turning
    self.drive(linear=0.0, angular=0.7)
```

Once the counter has reached the $2\pi$ limit, the neato has completed the full circle and the velocity commands are set to 0.

## Fetch using Object Detection
The last of our behaviors is fetch. The act of "fetching" for our D.A.W.G. is split up into two steps: searching and following. The searching step consists of the neato finding its toy. The "toy" we gave to our D.A.W.G. was a red expo marker. We chose a red expo marker since we figured it had a high amount of contrast that would be easy for the robot to detect. Given there is no red expo marker dataset, we decided to train our own custom model.

### YOLO 26 Custom dataset
Through researching, we found a helpful colab notebook that gave us all the commands we needed to train our own dataset. Our dataset includes 414 images, 16 of which do not include an expo marker. This helps teach the model what it looks like when the object is not there. We then used a 85-9-6 percent split for the training, validation, and testing of our images. Additionally, we resized the image sizes down to $640\times 640\text{ px}$.

![yolo diagram](neato_dog/images/Screenshot%20from%202026-11-10%2020-21-32.png)

These images were imported into roboflow, allowing us to create bounding boxes for each image that would be added to the dataset before we trained it.

414 images is a fairly small dataset, but it took an hour and a half to draw boxes around each individual image. To increase the size of our dataset without having to draw more images, we applied a few augmentations to each image. By applying flips, rotations, brightness adjustments, and blur, we ended with 960 images: 819 for training, 83 for validation, and 58 for testing. The percentage split was autogenerated by roboflow. Roboflow then gave us a custom link to paste into the colab notebook:

![roboflow diagram](neato_dog/images/Screenshot%20from%202026-11-10%2020-26-07.png)

```python
pip install roboflow
from roboflow import Roboflow
rf = Roboflow(api_key="...")
project = rf.workspace("montessoriar").project("expo-marker-yvkby")
version = project.version(2)
dataset = version.download("yolo26")
```

We then trained the dataset on 100 epochs. After each pass, it evaluates how well it did. If it was better than any previous pass, it was saved as the best. We retrieved the best run and now had a custom dataset to use!

### Testing
Before making the D.A.W.G. "fetch" there were two things we wanted to test: the neato's ability to follow an object, and how well the dataset worked on our basic webcam camera. To test the robot's aforementioned capabilities, we used much of the code given during the neato_soccer class assignment. This was tested entirely in the simulator as it was much easier to control the color of the objects in this environment.

The thresholding strategy is not important as that is borrowed code, and it would change in our implementation with the object detection model. One design decision we set in the initial implementation that went unused was threading. The initial strategy was to create an event handler that told the neato when the shape was found to switch between "searching" and "fetching." We kept this for a while but found it unnecessary and realized we could simply check whether or not there was an annotated box. This was already being checked to run a separate thread.

### Neato Movements
The actual movements of "searching" and "fetching" are very simple. To search, the D.A.W.G spins in a circle until the camera finds the desired object. To fetch, the robot locates the object, adds up all the x pixel positions of the object, and divides the total by all points to obtain the center x position. It then normalizes the value in terms of the pixels in the image. We do this by taking the center x, subtracting the width of half the image, and dividing that difference by the total width of the image.

```python
self.center_x, self.center_y = moments['m10']/moments['m00'], moments['m01']/moments['m00']
self.norm_x_pose = (self.center_x - self.cv_image.shape[1]/2) / self.cv_image.shape[1]
```

The angular velocity is then set to the negative of `self.norm_x_pose`. It is set as the negative because the `norm_x_pose` on the right side of the image will always be positive, but for the D.A.W.G to move in that position, the angular velocity has to be negative.

### Marker Detection
To confirm that our custom object detection dataset works, we created a script that works with our laptop's webcam. Ultralytics has a lot of great documentation on how to do Object Detection with Ultralytics.

The implementation was pretty simple. To access the image, we have to use OpenCV's "read()" method. This has two outputs. The first is a boolean that tells us whether we've retrieved the image successfully or not. The second is the image frame itself. To detect, we must first run the model:

```python
model = YOLO("neato_dog/YOLO_model/best.pt")
results = model(frame, stream=True)
```

Then use the "plot()" method from YOLO Ultralytics to determine whether or not our image contains the desired red expo marker.

```python
for result in results:
    annotated_frame = result.plot()
```

We then tell OpenCV to show our new annotated_frame, creating a bounding box.

![box diagram](neato_dog/images/Screenshot%20from%202026-11-10%2020-27-14.png)

### Implementation
Now we're at the actual fun part of the fetch behavior! We also found the Ultralytics documentation to be super helpful thanks to a YOLO with ROS Quickstart Guide. The most helpful method from this documentation was CvBridge. This allowed us to take a ROS message from the D.A.W.G camera and turn it into an OpenCV/Numpy array that YOLO could use, and then convert that back into a ROS image message that we can publish.

```python
self.cv_image = self.bridge.imgmsg_to_cv2(message, desired_encoding="bgr8")
```

This code section converts the ROS message into an image YOLO can run its object detection on.

```python
self.img_pub.publish(self.bridge.cv2_to_imgmsg(self.final, encoding="bgr8"))
```

This code section takes the annotated frame after the YOLO model has run, and returns it back to ROS under a topic we've previously defined in initialization:

```python
self.img_pub = self.create_publisher(Image, "ultralytics/detection/image", 5)
```

As mentioned previously in the testing section, we planned to have a multithread within the script that was no longer necessary during implementation This is because we control when a node is active using a separate node. The logic for how the D.A.W.G. makes the decision between its "searching" or "fetching" behaviors is nested in a simple if statement in the main loop.

```python
if len(result.boxes) == 0:  # YOLO finds nothing in frame
    self.final = frame
    self.drive(linear=0.0, angular=0.3)
else:
    # YOLO finds a red expo marker in frame
    x_center = float(result.boxes.xywh[0][0])  # boxes gives a tensor. Must convert to python number
    self.norm_x_pose = (x_center - self.cv_image.shape[1]/2) / self.cv_image.shape[1]
    self.final = result.plot()
    self.drive(linear=0.1, angular=-self.norm_x_pose)
```

### Finite State Machine
The gesture detection node is subscribed to the image topic, gathering camera feed to recognize our three pre-defined gestures. The state-switching logic is done using match and case statements inside this node. Our MediaPipe classifications, "Open Hand", "Zero", and "Peace Sign" act as event triggers which are then used by the match commands to decide which states are set to active or inactive. We used this method of mapping to eliminate the need for conditionals and simplify logic. Additionally, this allowed us to keep the state-switching code blocks in one file, unlike our previous conditionals that were planted inside each behavior node class. Each match case section sets a mutually exclusive state assignment, ensuring there are no overlapping active states and that only one behavior node is executing velocity commands at a time.

## Individual Learning Objections & Reflections

### Avani
This project allowed me to look into MediaPipe in a different way than I have before. I had used it for a previous project, but I didn't really work on it in that much depth. It was very interesting for me to learn how to use OpenCV and MediaPipe with ROS. I learned a lot about how to integrate computer vision into a physical robot. One big takeaway I had from this project was learning how to integrate with others. This project, I was able to focus on the hand gestures part and then come together with my project teammates to make the D.A.W.G. I learned about how to divide a project into even parts and make sure the code I wrote was able to integrate with theirs. This project was a great experience for me to learn about the basics of machine vision.

### Trevor
The past two projects I feel like I've understood the topics at a very surface level, and my goal for this project was to really have a strong understanding of what each function did and feel confident that I could do it again in half the time. The first very important step I took to this was starting early. For the FSM project, it was hard to start early because that project was much shorter and there were a lot of things to adapt to. For the particle filter, my partner and I both had a lot going on, and so we left it all until the Saturday before it was due. This project, we definitely had a much more balanced spread of work throughout the three weeks, and I felt like I was really making sure I was staying on top of my tasks.

Another really important step I took was to get more help from the teaching team and documentation. In the past when I was stuck, I would stare at the computer, maybe put a couple of print statements, check the class website to see if there was anything useful, and if there wasn't, I would probably end up using some AI tool for a bit of guidance. Since I was being proactive, it made it much easier to find the teaching team to help, and I had more time to read through documentation. Teaching support was especially helpful in creating our FSM, where Charlie outlined how we could create a control without creating a separate string topic that all nodes have to subscribe and publish to. Documentation was especially helpful for me when trying to link YOLO and ROS. Ultralytics had a very helpful documentation page that is linked above. Computer Vision is really fun!

### Vanessa
For this project, my main learning goal was to fully figure out how to write an FSM and odometry-based behaviors from scratch. Even though we worked with an FSM for our first project, my partner handled the state-switching logic, so writing it myself this time was completely new.

At first, it was a bit confusing trying to adapt the code to this project's architecture. In our first project, our state-switching was linear, meaning you had to transition sequentially through the states. But for our neato dog implementation, we needed the flexibility to jump from any state to any other state. When I tried to use the same structure from the first FSM, my conditional statements were tangled and bugged, and states wouldn't switch correctly due to overlapping logic. Thankfully, a CA suggested we use match and case blocks, making the logic simple and clear. Though I didn't write the CV code for this project, reading through the gesture code and talking it over with my teammates was a great refresher of my experience in FunRobo and I feel fully prepared to use computer vision in my final project.

## Bag Files
This bag file tracks the odometry (/odom) and velocity (/cmd_vel) topics. We were advised to not include the image data in our ros bag, so in addition to the bag file, we have attached the video we took simultaneously with the bag file.

To run the bag file in simulation, launch the gazebo world.
```bash
ros2 launch neato2_gazebo neato_gauntlet_world.py
```
Then, navigate to the right file location and run the ros bag. Here, we're only reading the velocity topic as to not confuse the odometry of the bag and of the gazebo simulator.
```bash
cd ~/ros2_ws/src/neato_dog
ros2 bag play neato_dog_demo --topics /cmd_vel
```
https://drive.google.com/file/d/1MKL_bKD-_mTbzabMfqgFPULfruPKo5GX/view?usp=sharing 

## Future Implementations
If we had more time, we would have liked to implement the stretch goal from our original proposal. Our goal was to have our D.A.W.G. follow a person. This would happen after the robot successfully finds and "picks up" the object it was trying to fetch. It would then search for the nearest person and follow them.

In our proposal, we had intended to use ZED 2i stereo cameras. A future, more complicated D.A.W.G. would use the stereo cameras to calculate the distance of various objects and that could inform what it should fetch if there were multiple "toys" in view. We also created scripts to calibrate our camera, and although they weren't used for this version of the D.A.W.G. they can be found in the testing_scripts for future use.

## How to run
In addition to all the other ros dependencies, there are a couple of things you must install to run the D.A.W.G.

The first of which is MediaPipe:  
*Note: An older version of MediaPipe must be installed. NumPy and OpenCV are pinned in the same command because installing MediaPipe would otherwise upgrade NumPy to version 2, which ROS 2 and Ubuntu's system packages are not compatible with. Newer versions of OpenCV also require NumPy 2. The `--break-system-packages` flag is needed because Ubuntu 24.04 blocks pip from installing into the system Python without it, and `--no-cache-dir` keeps the large download from filling up your disk.*

```bash
/usr/bin/python3 -m pip install "mediapipe==0.10.14" "numpy<2" "opencv-contrib-python<4.12" --break-system-packages --no-cache-dir
```

To run the YOLO detection model, you must also have the Ultralytics package. To do this, run the following command in your terminal.

```bash
pip install -U ultralytics
```

Another dependency is the `tf_transformations` package for our spin script. To do this, run
```bash
sudo apt install ros-jazzy-tf-transformations
```
(assuming you are using the jazzy distribution).

To run the program on the physical neato, first connect to it properly
```bash
ros2 launch neato_node2 bringup.py host:="YOUR_NEATO_IP"
```
Then, build and run `gesture_node.py`
```bash
colcon build --symlink-install --packages-select neato_dog
source install/setup.bash
ros2 run neato_dog gesture_node
```
You DO NOT need to run any of the other scripts.
