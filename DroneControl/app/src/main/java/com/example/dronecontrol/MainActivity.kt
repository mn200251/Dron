package com.example.dronecontrol

import android.app.NotificationManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.util.Log
import android.view.View
import android.view.WindowInsets
import android.view.WindowInsetsController
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.annotation.RequiresApi
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
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.State
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
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
import androidx.core.app.ActivityCompat
import androidx.core.view.ViewCompat.onApplyWindowInsets
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LiveData
import androidx.lifecycle.Observer
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.dronecontrol.screens.DroneScreen
import com.example.dronecontrol.screens.MainScreen
import com.example.dronecontrol.sharedRepositories.SharedRepository
import com.example.dronecontrol.screens.VideoListScreen
import com.example.dronecontrol.services.ConnectionService
import com.example.dronecontrol.ui.theme.DroneControlTheme
import com.example.dronecontrol.viewmodels.ConnectionViewModel
import com.example.dronecontrol.viewmodels.SCREEN
import com.example.dronecontrol.viewmodels.VideoViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlin.math.log

class MainActivity : ComponentActivity() {
    @RequiresApi(Build.VERSION_CODES.R)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        hideSystemUI()

        setContent {
            DroneControlTheme {
                DroneApp(this, this, this)
            }
        }
    }

    override fun onStop() {
        super.onStop()

        val screen = SharedRepository.screenNumber.value

        if (screen == SCREEN.DroneScreen) {
            val intent = Intent(this, ConnectionService::class.java).apply {
                this.action = "ACTION_APP_BACKGROUND"
            }

            startService(intent)
        }
    }

    override fun onRestart() {
        super.onRestart()

        val screen = SharedRepository.screenNumber.value

        if (screen == SCREEN.DroneScreen)
        {
            val intent = Intent(this, ConnectionService::class.java).apply {
                this.action = "ACTION_APP_FOREGROUND"
            }

            startService(intent)
        }
    }

    override fun onDestroy() {
        super.onDestroy()

        // distinguish between activity finishing and pausing
        if (isFinishing)
        {
            // stop connection service
            val intent = Intent(this, ConnectionService::class.java)
            stopService(intent)

            // cancel all notifications when exiting app
            val notificationManager = this.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.cancelAll()
        }
    }

    @RequiresApi(Build.VERSION_CODES.R)
    private fun hideSystemUI() {
        window.setDecorFitsSystemWindows(false)
        val controller = window.insetsController
        if (controller != null) {
            controller.hide(WindowInsets.Type.statusBars() or WindowInsets.Type.navigationBars())
            controller.systemBarsBehavior =
                WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        }
    }

    @RequiresApi(Build.VERSION_CODES.R)
    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) {
            hideSystemUI()
        }
    }
}




@RequiresApi(Build.VERSION_CODES.R)
@Composable
fun DroneApp(context: Context, lifeCyleOwner: LifecycleOwner, activity: MainActivity)
{
    var connectionViewModel: ConnectionViewModel = viewModel()

    // Convert LiveData to StateFlow or use a MutableState directly in Compose
    val screen by SharedRepository.screenNumber.collectAsState(SCREEN.MainScreen) // Use a default value

    // Observe screenNumber and update the screen accordingly
    UpdateScreen(screen, context, connectionViewModel, activity)

}

@Composable
fun <T> LiveData<T>.collectAsState(initial: T): State<T> {
    val state = remember { mutableStateOf(initial) }
    val observer = rememberUpdatedState(newValue = { value: T -> state.value = value })

    DisposableEffect(this) {
        val liveDataObserver = Observer<T> { value -> observer.value(value) }
        observeForever(liveDataObserver)
        onDispose { removeObserver(liveDataObserver) }
    }

    return state
}

@RequiresApi(Build.VERSION_CODES.O)
@Composable
private fun UpdateScreen(screen: SCREEN, context: Context, connectionViewModel: ConnectionViewModel = viewModel(), activity: MainActivity) {
    when (screen) {
        SCREEN.MainScreen -> {
            MainScreen(connectionViewModel, context, activity)
        }
        SCREEN.DroneScreen -> {
            DroneScreen(connectionViewModel, context)
        }

        SCREEN.VideoListScreen -> {
            VideoListScreen(viewModel = VideoViewModel(SavedStateHandle()))
        }
    }
}





