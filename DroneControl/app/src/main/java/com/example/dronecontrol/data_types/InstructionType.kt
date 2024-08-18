package com.example.dronecontrol.data_types

enum class InstructionType(val value: Int) {
    HEARTBEAT(1),
    START_RECORDING(2),
    STOP_RECORDING(3),
    START_FLIGHT(4),
    END_FLIGHT(5),
    GET_FLIGHTS(6),
    START_PREVIOUS_FLIGHT(7),
    GET_VIDEOS(8),
    DOWNLOAD_VIDEO(9),
    KILL_SWITCH(10),
    JOYSTICK(11),
    GET_LINK(12),
    TURN_OFF(13),
    GET_STATUS(14), // Check the status as some instructions might not have passed, e.g., start recording
    BACK(15) // Return from browsing videos/flights
}