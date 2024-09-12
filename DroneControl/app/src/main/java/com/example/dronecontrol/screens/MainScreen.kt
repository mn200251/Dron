package com.example.dronecontrol.screens

import android.Manifest.permission.POST_NOTIFICATIONS
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.RequiresApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shadow
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.app.ActivityCompat.finishAffinity
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.dronecontrol.MainActivity
import com.example.dronecontrol.R
import com.example.dronecontrol.collectAsState
import com.example.dronecontrol.sharedRepositories.SharedRepository
import com.example.dronecontrol.viewmodels.ConnectionViewModel
import com.example.dronecontrol.viewmodels.SCREEN
import kotlinx.coroutines.delay
import kotlin.system.exitProcess


@Composable
fun AnimatedBackground() {
    val zoomLevel = 1.1f // 15% zoom

    // State for panning
    var offsetX by remember { mutableStateOf(0f) }
    var offsetY by remember { mutableStateOf(0f) }

    // Animation parameters
    val maxOffsetX = 100f
    val maxOffsetY = 30f

    var speedX = 0.2f // Speed of panning
    var speedY = 0.07f // Speed of panning

    // Animate panning
    LaunchedEffect(Unit) {
        while (true) {
            offsetX += speedX
            if (offsetX > maxOffsetX || offsetX < -maxOffsetX) {
                speedX *= -1 // Reverse direction when hitting edge
            }

            offsetY += speedY
            if (offsetY > maxOffsetY || offsetY < -maxOffsetY) {
                speedY *= -1 // Reverse direction when hitting edge
            }

            delay(16) // 60 FPS
        }
    }

    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        Image(
            painter = painterResource(id = R.drawable.background_image3),
            contentDescription = "Main Screen Background Image",
            contentScale = ContentScale.Crop,
            modifier = Modifier
                .fillMaxSize()
                .graphicsLayer(
                    scaleX = zoomLevel,
                    scaleY = zoomLevel,
                    translationX = offsetX,
                    translationY = offsetY
                )
        )
    }
}

@RequiresApi(Build.VERSION_CODES.O)
@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun MainScreen(connectionViewModel: ConnectionViewModel = viewModel(), context: Context, activity: MainActivity) {
    val titleFontSize: TextUnit = 46.sp
    // val titleFont: Font =
    val textFontSize: TextUnit = 20.sp

    val uiState by connectionViewModel.uiState.collectAsState()
    val keyboardController = LocalSoftwareKeyboardController.current

    val buttonModifier = Modifier
        .width(180.dp)
        .height(35.dp)

    val spaceModifier = Modifier.height(11.dp)
    val buttonTransparency = 0.8f

    val mainScreenErrorText by SharedRepository.mainScreenErrorText.collectAsState("")

    val currContext = LocalContext.current

    val requestPermissionLauncherVideoListScreen = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isPermissionGranted ->
        if (isPermissionGranted) {
            connectionViewModel.updateScreenNumber(SCREEN.VideoListScreen)
        }
    }

    val requestPermissionLauncherDroneScreen = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isPermissionGranted ->
        if (isPermissionGranted) {
            connectionViewModel.startService(context, "ACTION_APP_FOREGROUND")
        }
    }

    Box(
        modifier = Modifier.fillMaxSize()
    ) {
//        Image(
//            painter = painterResource(id = R.drawable.background_image3),
//            contentDescription = "Main Screen Background Image",
//            contentScale = ContentScale.Crop, // or ContentScale.FillBounds
//            modifier = Modifier.fillMaxSize()
//        )

        AnimatedBackground()

        Column(
            modifier = Modifier
                .fillMaxSize()
                // .padding(horizontal = 5.dp)
                .clickable {
                    keyboardController?.hide()
                },
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "DroneControl App",
                fontFamily = FontFamily.Default, // Use FontFamily.Default if you have no custom font
                fontWeight = FontWeight.Bold,
                fontSize = titleFontSize, // Adjust the size as needed
                color = Color.Gray, // Primary color of the text
                style = TextStyle(
                    shadow = Shadow(
                        color = Color.Black, // Outline color
                        offset = Offset(12f, 12f),
                        blurRadius = 16f
                    )
                ),
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(40.dp))

            Button(
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(128, 128, 128)
                ),
                onClick = {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        if (ContextCompat.checkSelfPermission(
                                currContext,
                                POST_NOTIFICATIONS
                            ) != PackageManager.PERMISSION_GRANTED
                        ) {
                            requestPermissionLauncherDroneScreen.launch(POST_NOTIFICATIONS)
                        } else {
                            connectionViewModel.startService(context, "ACTION_APP_FOREGROUND")
                        }
                    } else {
                        connectionViewModel.startService(context, "ACTION_APP_FOREGROUND")
                    }
                          },
                modifier = buttonModifier
                    .align(Alignment.CenterHorizontally)
                    .alpha(buttonTransparency),
                ) {
                Text("Start", fontSize = textFontSize, fontWeight = FontWeight.Bold,
                    color = Color.Black)
            }

            Spacer(modifier = spaceModifier)

            Button(
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(128, 128, 128)
                ),
                onClick = {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                        if (ContextCompat.checkSelfPermission(
                                currContext,
                                POST_NOTIFICATIONS
                            ) != PackageManager.PERMISSION_GRANTED
                        ) {
                            requestPermissionLauncherVideoListScreen.launch(POST_NOTIFICATIONS)
                        } else {
                            connectionViewModel.updateScreenNumber(SCREEN.VideoListScreen)
                        }
                    } else {
                        connectionViewModel.updateScreenNumber(SCREEN.VideoListScreen)
                    }
                },
                modifier = buttonModifier
                    .align(Alignment.CenterHorizontally)
                    .alpha(buttonTransparency),

                ) {
                Text("Saved videos", fontSize = textFontSize, fontWeight = FontWeight.Bold,
                    color = Color.Black)
            }

            Spacer(modifier = spaceModifier)

            Button(
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(128, 128, 128)
                ),
                onClick = {
                    finishAffinity(activity)
                    exitProcess(0)
                },
                modifier = buttonModifier
                    .align(Alignment.CenterHorizontally)
                    .alpha(buttonTransparency),

                ) {
                Text("Exit", fontSize = textFontSize, fontWeight = FontWeight.Bold,
                    color = Color.Black)
            }

            Spacer(modifier = spaceModifier)

//            if (mainScreenErrorText != "")
//            {
                Text(text = mainScreenErrorText,
                    fontSize = 26.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.Red,
                    style = TextStyle(
                        shadow = Shadow(
                            color = Color.Black, // Outline color
                            offset = Offset(10f, 10f),
                            blurRadius = 14f
                        )
                    ))
//            }
        }
    }
}