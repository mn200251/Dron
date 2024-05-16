package com.example.dronecontrol.viewmodels

import android.os.Parcelable
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.parcelize.Parcelize


@Parcelize
data class ConnectionState(
    var host: String = "",
    var port: String = "",
    var mainScreenErrorText: String = "",
) : Parcelable

const val UI_STATE_KEY = "uiState"

class ConnectionViewModel(private val savedStateHandle: SavedStateHandle) : ViewModel() {

    private val _uiState1 = MutableStateFlow(ConnectionState())

    private val _uiState2 = savedStateHandle.getStateFlow(UI_STATE_KEY, ConnectionState())

    val uiState = _uiState2




    fun updateHost(newHost: String)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            host = newHost,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                host = newHost,
            )
        }
    }

    fun updatePort(newPort: String)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            port = newPort,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                port = newPort,
            )
        }
    }

    fun updateMainScreenErrorText(newError:String)
    {
        savedStateHandle[UI_STATE_KEY] = _uiState2.value.copy(
            mainScreenErrorText = newError,
        )
        _uiState1.update { currentConnectionUiState ->
            currentConnectionUiState.copy(
                mainScreenErrorText = newError,
            )
        }
    }
}