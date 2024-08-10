package com.example.dronecontrol.viewmodels

import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Parcelable
import android.util.Log
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.core.content.ContextCompat
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.dronecontrol.collectAsState
import com.example.dronecontrol.services.ConnectionService
import com.example.dronecontrol.sharedRepositories.SharedRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.parcelize.Parcelize
import kotlinx.serialization.Serializable
import java.io.DataInputStream
import java.io.InputStream
import java.net.Socket


@Parcelize
data class ConnectionState(
    // var host: String = "",
    // var port: String = "",
    // var mainScreenErrorText: String = "",
    // var screenNumber: SCREEN = SCREEN.MainScreen,

    var joystickX: Float = 0f,
    var joystickY: Float = 0f,
    var joystickZ: Float = 0f,
    var joystickRotation: Float = 0f,

    var isSendingMovement: Boolean = false,
    // var connectionActive: Boolean = false,

    // var frame: Bitmap? = null,

    var monitorMovementBoolean: Boolean = false,

    // @RawValue var socket: Socket? = null
) : Parcelable

const val UI_STATE_KEY = "uiState"

enum class SCREEN{
    MainScreen,
    DroneScreen
}

@Serializable
data class Coordinates(val x: Float, val y: Float, val z: Float, val rotation: Float)


@Parcelize
@Serializable
data class Controls(val x: Float, val y: Float, val z: Float, val rotation: Float) : Parcelable


class ConnectionViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel() {

    private val _uiState1 = MutableStateFlow(ConnectionState())

    private val _uiState2 = savedStateHandle.getStateFlow(UI_STATE_KEY, ConnectionState())

    val uiState = _uiState2

    fun startService(context: Context, action: String) {
        Log.d("ViewModel", "Usao u startService")
        val intent = Intent(context, ConnectionService::class.java).apply {
            this.action = action
        }

        context.startService(intent)

        setMonitorMovementBoolean(true)

        viewModelScope.launch(Dispatchers.Default)
        {
            monitorControls(context)
        }

        Log.d("ViewModel", "Zavrsio u startService")
    }

    private fun setMonitorMovementBoolean(newValue: Boolean)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            monitorMovementBoolean = newValue,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                monitorMovementBoolean = newValue,
            )
        }
    }

    /*
    private fun updateScreen(newScreen: SCREEN)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            screenNumber = newScreen,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                screenNumber = newScreen,
            )
        }
    }
     */

    // Updating the shared data through the repository
    fun updateFrame(newFrame: Bitmap?) {
        SharedRepository.setFrame(newFrame)
    }

    fun updateMainScreenErrorText(errorText: String) {
        SharedRepository.setMainScreenErrorText(errorText)
    }

    fun updateScreenNumber(newScreenNumber: SCREEN) {
        SharedRepository.setScreen(newScreenNumber)
    }


    // x and y are normalized to 0-1
    fun updateRightJoystickMovement(x: Float, y: Float)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            joystickX = x,
            joystickY = y,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                joystickX = x,
                joystickY = y,
            )
        }

        if (uiState.value.joystickX == 0f && uiState.value.joystickY == 0f &&
            uiState.value.joystickZ == 0f && uiState.value.joystickRotation == 0f)
            updateIsSendingMovement(false)
        else
            updateIsSendingMovement(true)
    }

    fun updateLeftJoystickMovement(normalizedX: Float, normalizedY: Float) {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            joystickZ = normalizedX,
            joystickRotation = normalizedY,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                joystickZ = normalizedX,
                joystickRotation = normalizedY,
            )
        }

        if (uiState.value.joystickX == 0f && uiState.value.joystickY == 0f &&
            uiState.value.joystickZ == 0f && uiState.value.joystickRotation == 0f)
            updateIsSendingMovement(false)
        else
            updateIsSendingMovement(true)
    }

    private fun updateIsSendingMovement(isSendingMovement: Boolean)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            isSendingMovement = isSendingMovement
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                isSendingMovement = isSendingMovement
            )
        }
    }

    private fun resetControls()
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            joystickX = 0f,
            joystickY = 0f,
            joystickZ = 0f,
            joystickRotation = 0f,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                joystickX = 0f,
                joystickY = 0f,
                joystickZ = 0f,
                joystickRotation = 0f,
            )
        }
    }

    /*
    fun updateFrame(newFrame: Bitmap)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            frame = newFrame
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                frame = newFrame
            )
        }
    }
    */


    private fun sendControls2Service(context: Context, action: String)
    {
        val controls = Controls(uiState.value.joystickX, uiState.value.joystickY,
            uiState.value.joystickZ, uiState.value.joystickRotation)

        val intent = Intent(context, ConnectionService::class.java).apply {
            this.action = action
            putExtra("ControlData", controls)
        }
        context.startService(intent)

        // ContextCompat.startForegroundService(context, intent)
    }

    // ako se ugasi konekcija i startuje nova STVORICE MEMORY LEAK!\
    // ne moze Job da se cuva u data class
    // ah
    suspend fun monitorControls(context: Context)
    {
        while (uiState.value.monitorMovementBoolean)
        {
            if (uiState.value.isSendingMovement)
            {
                sendControls2Service(context, "ACTION_APP_FOREGROUND")
            }

            delay(30)
        }
    }

}