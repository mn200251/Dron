package com.example.dronecontrol.screens

import android.app.Activity
import android.content.Context
import android.graphics.fonts.Font
import android.os.Build
import androidx.annotation.RequiresApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shadow
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.app.ActivityCompat.finishAffinity
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.dronecontrol.MainActivity
import com.example.dronecontrol.R
import com.example.dronecontrol.collectAsState
import com.example.dronecontrol.sharedRepositories.SharedRepository
import com.example.dronecontrol.viewmodels.ConnectionViewModel
import com.example.dronecontrol.viewmodels.SCREEN
import kotlin.system.exitProcess


@RequiresApi(Build.VERSION_CODES.O)
@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun MainScreen(connectionViewModel: ConnectionViewModel = viewModel(), context: Context, activity: MainActivity) {
    val titleFontSize: TextUnit = 43.sp
    // val titleFont: Font =
    val textFontSize: TextUnit = 20.sp

    val uiState by connectionViewModel.uiState.collectAsState()
    val keyboardController = LocalSoftwareKeyboardController.current

    val buttonModifier = Modifier
        .width(180.dp)
        .height(35.dp)

    val spaceModifier = Modifier.height(10.dp)

    val mainScreenErrorText by SharedRepository.mainScreenErrorText.collectAsState("")

    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        Image(
            painter = painterResource(id = R.drawable.background_image3),
            contentDescription = null,
            contentScale = ContentScale.Crop, // or ContentScale.FillBounds
            modifier = Modifier.fillMaxSize()
        )

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
                        offset = Offset(10f, 10f),
                        blurRadius = 14f
                    )
                ),
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(30.dp))

            Button(
                onClick = { connectionViewModel.startService(context, "ACTION_APP_FOREGROUND") },
                modifier = buttonModifier.align(Alignment.CenterHorizontally),

                ) {
                Text("Start", fontSize = textFontSize)
            }

            Spacer(modifier = spaceModifier)

            Button(
                onClick = {
                    connectionViewModel.updateScreenNumber(SCREEN.VideoListScreen)
                },
                modifier = buttonModifier.align(Alignment.CenterHorizontally),

                ) {
                Text("Saved videos", fontSize = textFontSize)
            }

            Spacer(modifier = spaceModifier)

            Button(
                onClick = {
                    finishAffinity(activity)
                    exitProcess(0)
                },
                modifier = buttonModifier.align(Alignment.CenterHorizontally),

                ) {
                Text("Exit", fontSize = textFontSize)
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