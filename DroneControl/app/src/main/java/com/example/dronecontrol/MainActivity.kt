package com.example.dronecontrol

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.runtime.Composable
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.dronecontrol.screens.DroneScreen
import com.example.dronecontrol.screens.MainScreen
import com.example.dronecontrol.ui.theme.DroneControlTheme
import com.example.dronecontrol.viewmodels.ConnectionViewModel
import com.example.dronecontrol.viewmodels.SCREEN
import kotlinx.coroutines.flow.MutableStateFlow
import kotlin.math.log

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            DroneControlTheme {

                DroneApp()
            }
        }
    }
}

@Composable
fun DroneApp()
{
    var connectionViewModel: ConnectionViewModel = viewModel()
    val uiState by connectionViewModel.uiState.collectAsState()

    when (uiState.screenNumber)
    {
        SCREEN.MainScreen -> MainScreen(connectionViewModel)
        SCREEN.DroneScreen -> DroneScreen(connectionViewModel)
        else -> {
            Log.d("Error", "Screen does not exist!")
        }
    }
}





