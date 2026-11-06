from setuptools import find_packages, setup

package_name = 'neato_dog'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='trevor',
    maintainer_email='trevor.e.mcdonald@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'fetch = neato_dog.fetch:main',
            'sit = neato_dog.sit:main',
            'YOLO_fetch = neato_dog.YOLO_fetch:main',
            'spin = neato_dog.spin:main',
            'finite_state_machine = neato_dog.finite_state_machine:main',
            'take_pictures = neato_dog.take_pictures:main',
            'neato_cam_calibration = neato_dog.neato_cam_calibration:main',
            'gesture_node = neato_dog.gesture_node:main',
            'hand_gestures = neato_dog.hand_gestures:main'
        ],
    },
)
