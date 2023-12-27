package com.example.phonedelaytest

import android.os.Bundle
import android.view.MotionEvent
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.gestures.PressGestureScope
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.phonedelaytest.ui.theme.PhoneDelayTestTheme
import com.example.phonedelaytest.viewmodels.ConnectionViewModel
import com.example.phonedelaytest.viewmodels.ControlsEnum

import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.pointerInteropFilter
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            PhoneDelayTestTheme {
                // A surface container using the 'background' color from the theme
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {

                    PhoneDelayTest()
                }
            }
        }
    }
}


@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun PhoneDelayTest(viewModel: ConnectionViewModel = viewModel())
{
    viewModel.startController()
    var jobUp by remember { mutableStateOf<Job?>(null) }
    var jobDown by remember { mutableStateOf<Job?>(null) }
    var jobLeft by remember { mutableStateOf<Job?>(null) }
    var jobRight by remember { mutableStateOf<Job?>(null) }


    val waitPressed: Long = 10

    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Spacer(modifier = Modifier.size(32.dp)) // Add some space above the buttons
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.padding(vertical = 8.dp)
            ) {
                Row(horizontalArrangement = Arrangement.Center) {
                    Button(
                        onClick = {
                                  // viewModel.updateControls(ControlsEnum.UP)
                             },
                        modifier = Modifier.size(100.dp).pointerInteropFilter { event ->
                            when (event.action) {
                                MotionEvent.ACTION_DOWN -> {
                                    jobUp?.cancel()
                                    jobUp = CoroutineScope(Dispatchers.Default).launch {
                                        while (true) {
                                            viewModel.updateControls(ControlsEnum.UP)
                                            delay(waitPressed)
                                        }
                                    }
                                }
                                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                                    jobUp?.cancel()
                                }
                            }
                            true

                        }
                    ) {
                        Text("UP")
                    }
                }
                Row(
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Button(
                        onClick = {
                            // viewModel.updateControls(ControlsEnum.LEFT)
                                  },
                        modifier = Modifier.size(100.dp).pointerInteropFilter { event ->
                            when (event.action) {
                                MotionEvent.ACTION_DOWN -> {
                                    jobLeft?.cancel()
                                    jobLeft = CoroutineScope(Dispatchers.Default).launch {
                                        while (true) {
                                            viewModel.updateControls(ControlsEnum.LEFT)
                                            delay(waitPressed)
                                        }
                                    }
                                }
                                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                                    jobLeft?.cancel()
                                }
                            }
                            true

                        }

                    ) {
                        Text("LEFT")
                    }
                    Spacer(modifier = Modifier.size(64.dp)) // Add space between left and right buttons
                    Button(
                        onClick = {
                            //viewModel.updateControls(ControlsEnum.RIGHT)
                                  },
                        modifier = Modifier.size(100.dp).pointerInteropFilter { event ->
                            when (event.action) {
                                MotionEvent.ACTION_DOWN -> {
                                    jobRight?.cancel()
                                    jobRight = CoroutineScope(Dispatchers.Default).launch {
                                        while (true) {
                                            viewModel.updateControls(ControlsEnum.RIGHT)
                                            delay(waitPressed)
                                        }
                                    }
                                }
                                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                                    jobRight?.cancel()
                                }
                            }
                            true

                        }


                    ) {
                        Text("RIGHT")
                    }
                }
                Row(horizontalArrangement = Arrangement.Center) {
                    Button(
                        onClick = {
                            // viewModel.updateControls(ControlsEnum.DOWN)
                                  },
                        modifier = Modifier.size(100.dp).pointerInteropFilter { event ->
                            when (event.action) {
                                MotionEvent.ACTION_DOWN -> {
                                    jobDown?.cancel()
                                    jobDown = CoroutineScope(Dispatchers.Default).launch {
                                        while (true) {
                                            viewModel.updateControls(ControlsEnum.DOWN)
                                            delay(waitPressed)
                                        }
                                    }
                                }
                                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                                    jobDown?.cancel()
                                }
                            }
                            true

                        }


                    ) {
                        Text("DOWN")
                    }
                }
            }
        }
    }

}