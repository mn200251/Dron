package com.example.dronecontrol.screens

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color.rgb
import android.graphics.Paint
import android.os.Build
import android.util.Log
import android.widget.Toast
import androidx.annotation.RequiresApi
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.input.pointer.PointerInputScope
import androidx.compose.ui.input.pointer.changedToDown
import androidx.compose.ui.input.pointer.changedToUp
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.positionChanged
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.times
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.dronecontrol.R
import com.example.dronecontrol.collectAsState
import com.example.dronecontrol.models.ModifiedJoyStick
import com.example.dronecontrol.sharedRepositories.SharedRepository
import com.example.dronecontrol.utils.InputDialog
import com.example.dronecontrol.utils.MacroSelectionDialog
import com.example.dronecontrol.viewmodels.ConnectionViewModel
import com.example.dronecontrol.viewmodels.MacroViewModel
import com.example.dronecontrol.viewmodels.SCREEN
import kotlin.math.roundToInt
import kotlin.math.sqrt


@RequiresApi(Build.VERSION_CODES.O)
@Composable
fun DroneScreen(
    connectionViewModel: ConnectionViewModel = viewModel(),
    macroViewModel: MacroViewModel = viewModel(),
    context: Context)
{
    val macroUiState by macroViewModel.uiState.collectAsState()

    val width = LocalConfiguration.current.screenWidthDp.dp
    val height = LocalConfiguration.current.screenHeightDp.dp

    var rightJoystickVisible by remember { mutableStateOf(false) }
    var leftJoystickVisible by remember { mutableStateOf(false) }

    var leftJoystickPosition by remember { mutableStateOf(Offset(0f, 0f)) }
    var rightJoystickPosition by remember { mutableStateOf(Offset(0f, 0f)) }

    var rightDotPosition by remember { mutableStateOf(Offset(0f, 0f)) }
    var leftDotPosition by remember { mutableStateOf(Offset(0f, 0f)) }

    val frame by SharedRepository.frame.collectAsState(null) // Use a default value
    
    val isPoweredOn by SharedRepository.isPoweredOn.collectAsState(initial = false)
    val isPidOn by SharedRepository.isPidOn.collectAsState(initial = false)
    val isRecordingMacro by SharedRepository.isRecordingMacro.collectAsState(initial = false)
    val isRecordingVideo by SharedRepository.isRecordingVideo.collectAsState(initial = false)

    val joystickAreaWidth = 0.45f
    val joystickAreaHeight = 0.65f

    val joystickSize = 160

    var showMacroDialog by remember { mutableStateOf(false) }
    var showVideoDialog by remember { mutableStateOf(false) }
    var showMacroSelectionDialog by remember { mutableStateOf(false) }

    val buttonSize = 70.dp


    Canvas(modifier = Modifier.fillMaxSize()) {
        frame?.let { bitmap: Bitmap ->
            val canvasWidth = size.width
            val canvasHeight = size.height

            val imageWidth = bitmap.width
            val imageHeight = bitmap.height

            val scaleX = canvasWidth / imageWidth
            val scaleY = canvasHeight / imageHeight
            val scale = kotlin.math.max(scaleX, scaleY)

            withTransform({
                scale(scale, scale, pivot = Offset.Zero)
            }) {
                drawImage(bitmap.asImageBitmap(), topLeft = Offset.Zero)
            }
        }
    }

    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        Row(
            modifier = Modifier
                .padding(start = 14.dp, top = 14.dp)
        ) {
            IconButton(
                onClick = {
//                val intent: Intent = Intent(context, ConnectionService::class.java)
//                context.stopService(intent)
                    connectionViewModel.stopService(context)

                    SharedRepository.setScreen(SCREEN.MainScreen)
                },
                modifier = Modifier
                    //.align(Alignment.TopStart)
                    //.padding(start = 14.dp, top = 14.dp)
                    .size(buttonSize)
            ) {
                Icon(
                    painter = painterResource(id = R.drawable.exit_icon),
                    contentDescription = "Exit Button Icon",
                    tint = Color(64, 64, 64, 75),
                )
            }
            
            Spacer(modifier = Modifier.padding(15.dp))

            Box(
                modifier = Modifier
                    .padding(start = 14.dp)
                    .size(buttonSize)
                    .pointerInput(Unit) {
                        detectTapGestures(
                            onLongPress = {
                                connectionViewModel.updatePoweredOn(context, !isPoweredOn)
                            }
                        )
                    }
            ) {
                Icon(
                    painter = painterResource(id = R.drawable.power_button),
                    contentDescription = "Power Button Icon",
                    tint = if (isPoweredOn) Color(0, 255, 0, 75)
                    else Color(255, 0, 0, 75),
                )
            }
        }

        IconButton(
            onClick = {
                connectionViewModel.updateIsPidOn(
                    context,
                    !isPidOn,
                )
            },
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(top = 12.dp, end = 14.dp + 2 * buttonSize + 30.dp)
                .padding(start = 10.dp)
                .size(buttonSize)
        ) {
            Icon(
                painter = painterResource(id = R.drawable.pid_button),
                contentDescription = "PID Button Icon",
                tint = if (isPidOn) Color(0, 255, 0, 75)
                else Color(255, 0, 0, 75),
            )
        }

        IconButton(
            onClick = {

                if (!isRecordingMacro)
                    showMacroDialog = true
                else
                    connectionViewModel.updateIsRecordingMacro(
                        context,
                        !isRecordingMacro,
                    )
            },
            enabled = isPoweredOn,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(top = 14.dp, end = 14.dp + buttonSize + 14.dp)
                .padding(start = 10.dp)
                .size(buttonSize)
        ) {
            Icon(
                painter = painterResource(id = R.drawable.flight_button),
                contentDescription = "Macro Button Icon",
                tint =
                    if (!isRecordingMacro) Color(0, 0, 0, 75)
                    else Color(255, 0, 0, 75),
            )
        }

        IconButton(
            onClick = {
                macroViewModel.fetchMacros()
                showMacroSelectionDialog = true
            },
            enabled = isPoweredOn,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(top = 14.dp, end = 14.dp)
                .padding(start = 14.dp)
                .size(buttonSize)
        ) {
            Icon(
                painter = painterResource(id = R.drawable.replay_icon),
                contentDescription = "Replay Button Icon",
                tint = Color(64, 64, 64, 75),
            )
        }

        IconButton(
            onClick = {
                if (!isRecordingVideo)
                    showVideoDialog = true
                else
                    connectionViewModel.updateIsRecordingVideo(
                        context,
                        !isRecordingVideo,
                        null
                    )

                // connectionViewModel.updateIsRecordingVideo(context,!isRecordingVideo)
            },
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(top = 78.dp, end = 14.dp)
                .padding(start = 14.dp)
                .size(buttonSize)
        ) {
            Icon(
                painter = painterResource(id = R.drawable.recording_button),
//                    if (uiState.isRecordingVideo) R.drawable.recording_button_running
//                    else R.drawable.recording_button),
                contentDescription = "Recording Button Icon",
                tint =
                    if (!isRecordingVideo) Color(0, 0, 0, 75)
                    else Color(255, 0, 0, 75),
                // modifier = iconModifier
            )
        }


        with(LocalDensity.current) {
            val screenWidthDp = LocalConfiguration.current.screenWidthDp.dp
            val screenHeightDp = LocalConfiguration.current.screenHeightDp.dp

            Box(
                modifier = Modifier
                    .align(Alignment.BottomStart)
                    .size(
                        width = joystickAreaWidth * screenWidthDp,
                        height = joystickAreaHeight * screenHeightDp
                    )
                    .pointerInput(Unit) {
                        detectMultitouchGestures(
                            joystickSize = joystickSize,
                            setVisible = { leftJoystickVisible = it },
                            setPosition = { leftJoystickPosition = it },
                            setDotPosition = { leftDotPosition = it },
                            updateMovement = { x, y ->
                                connectionViewModel.updateLeftJoystickMovement(
                                    x,
                                    y
                                )
                            },
                            stopMovement = {
                                connectionViewModel.updateLeftJoystickMovement(
                                    0f,
                                    0f
                                )
                            },
                            joystickVisible = { leftJoystickVisible },
                            joystickPosition = { leftJoystickPosition }
                        )
                    }
            ) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Your column content here
                }

                if (leftJoystickVisible) {
                    ModifiedJoyStick(
                        modifier = Modifier
                            .offset {
                                IntOffset(
                                    leftJoystickPosition.x.roundToInt() - 250,
                                    leftJoystickPosition.y.roundToInt() - 250
                                )
                            } // Adjust the offset to center the joystick
                            .size(joystickSize.dp)
                            .padding(30.dp),
                        size = joystickSize.dp,
                        dotSize = (joystickSize / 6).dp,
                        dotOffset = leftDotPosition
                    ) { x: Float, y: Float ->
                        Log.d("Left Joystick", "$x, $y")
                    }
                }
            }

            Box(
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .size(
                        width = joystickAreaWidth * screenWidthDp,
                        height = joystickAreaHeight * screenHeightDp
                    )
                    .pointerInput(Unit) {
                        detectMultitouchGestures(
                            joystickSize = joystickSize,
                            setVisible = { rightJoystickVisible = it },
                            setPosition = { rightJoystickPosition = it },
                            setDotPosition = { rightDotPosition = it },
                            updateMovement = { x, y ->
                                connectionViewModel.updateRightJoystickMovement(
                                    x,
                                    y
                                )
                            },
                            stopMovement = {
                                connectionViewModel.updateRightJoystickMovement(
                                    0f,
                                    0f
                                )
                            },
                            joystickVisible = { rightJoystickVisible },
                            joystickPosition = { rightJoystickPosition }
                        )
                    }
            ) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    verticalArrangement = Arrangement.Center,
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Your column content here
                }

                if (rightJoystickVisible) {
                    ModifiedJoyStick(
                        modifier = Modifier
                            .offset {
                                IntOffset(
                                    rightJoystickPosition.x.roundToInt() - 250,
                                    rightJoystickPosition.y.roundToInt() - 250
                                )
                            } // Adjust the offset to center the joystick
                            .size(joystickSize.dp)
                            .padding(30.dp),
                        size = joystickSize.dp,
                        dotSize = (joystickSize / 6).dp,
                        dotOffset = rightDotPosition
                    ) { x: Float, y: Float ->
                        Log.d("Right Joystick", "$x, $y")
                    }
                }
            }
        }

        if (showMacroDialog)
        {
            InputDialog(
                onConfirm = { name ->

                        connectionViewModel.updateIsRecordingMacro(
                            context,
                            !isRecordingMacro,
                            name
                        )

                        showMacroDialog = false
            },
                onDismiss = {
                    showMacroDialog = false
                },
                title = "Enter macro name")
        }

        if (showVideoDialog)
        {
            InputDialog(
                onConfirm = { name ->

                    connectionViewModel.updateIsRecordingVideo(
                        context,
                        !isRecordingVideo,
                        name
                    )

                    showVideoDialog = false
                },
                onDismiss = {
                    showVideoDialog = false
                },
                title = "Enter video name")
        }

        if (showMacroSelectionDialog) {
            MacroSelectionDialog(
                // strings = listOf("Item 1", "Item 2", "Item 3", "item 4", "item5", "item6", "item7"),
                macros = macroUiState.macroList,
                isLoading = macroUiState.isLoading,
                onConfirm = { selectedMacroName ->
                    connectionViewModel.startMacro(context, selectedMacroName)

                    val toast = Toast(context)
                    toast.setText("Macro started!")
                    toast.show()

                    showMacroSelectionDialog = false
                },
                onDismiss = { showMacroSelectionDialog = false } // Close the popup
            )
        }
    }
}

suspend fun PointerInputScope.detectMultitouchGestures(
    joystickSize: Int,
    setVisible: (Boolean) -> Unit,
    setPosition: (Offset) -> Unit,
    setDotPosition: (Offset) -> Unit,
    updateMovement: (Float, Float) -> Unit,
    stopMovement: () -> Unit,
    joystickVisible: () -> Boolean,
    joystickPosition: () -> Offset,
) {
    val adjustmentOffset = joystickSize / 4f

    awaitPointerEventScope {
        while (true) {
            val event = awaitPointerEvent()

            event.changes.forEach { change ->
                when {
                    change.changedToDown() -> {
                        setVisible(true)
                        setPosition(change.position)
                        setDotPosition(Offset(adjustmentOffset, adjustmentOffset))
                    }
                    change.changedToUp() -> {
                        setVisible(false)
                        stopMovement()
                    }
                    change.positionChanged() -> {
                        if (joystickVisible()) {
                            val maxOffset: Float = (joystickSize / 4).dp.toPx()
                            val x = change.position.x - joystickPosition().x
                            val y = change.position.y - joystickPosition().y
                            val distance = sqrt(x * x + y * y)
                            val constrainedX =
                                if (distance > maxOffset) x * (maxOffset / distance) else x
                            val constrainedY =
                                if (distance > maxOffset) y * (maxOffset / distance) else y
                            setDotPosition(
                                Offset(
                                    constrainedX + adjustmentOffset,
                                    constrainedY + adjustmentOffset
                                )
                            )

                            val normalizedX = (constrainedX) / maxOffset
                            val normalizedY = (constrainedY) / maxOffset

                            updateMovement(normalizedX, normalizedY)
                        }
                    }
                }
                change.consume()
            }
        }
    }
}

fun createDummyBitmap(width: Dp, height: Dp, i: Int): ImageBitmap {
    // val width = LocalConfiguration.current.screenWidthDp.dp
    // val height = LocalConfiguration.current.screenHeightDp.dp
    val width2 = 3150
    val height2 = 1450

    val bitmap = Bitmap.createBitmap(width2, height2, Bitmap.Config.ARGB_8888)
    val canvas = android.graphics.Canvas(bitmap)

    // Draw dummy content on the canvas
    canvas.drawColor(rgb(i - 70, i - 140, i))
    // rectangle
    canvas.drawRect(0f + 10 * i, 0f, 200f + 10f * i, 150f, Paint().apply { color = rgb(255 - i * 4, i, 0) })

    return bitmap.asImageBitmap()
}
