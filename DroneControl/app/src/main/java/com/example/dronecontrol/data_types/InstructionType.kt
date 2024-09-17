package com.example.dronecontrol.data_types

enum class InstructionType(val value: Int) {
    HEARTBEAT(1),
    START_RECORDING_VIDEO(2),
    STOP_RECORDING_VIDEO(3),
    START_RECORDING_MACRO(4),
    STOP_RECORDING_MACRO(5),
    GET_MACROS(6),
    START_MACRO(7),
    GET_VIDEOS(8),
    DOWNLOAD_VIDEO(9),
    TURN_ON(10),
    JOYSTICK(11),
    GET_LINK(12),
    TURN_OFF(13),
    GET_STATUS(14), // Check the status as some instructions might not have passed, e.g., start recording
    BACK(15), // Return from browsing videos/flights
}