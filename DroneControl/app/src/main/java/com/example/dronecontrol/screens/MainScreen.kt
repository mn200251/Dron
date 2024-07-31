package com.example.dronecontrol.screens

import android.os.Build
import androidx.annotation.RequiresApi
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.dronecontrol.viewmodels.ConnectionViewModel


@RequiresApi(Build.VERSION_CODES.O)
@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun MainScreen(connectionViewModel: ConnectionViewModel = viewModel()) {
    val inputFieldWidth: Dp = 500.dp
    val titleFontSize: TextUnit = 30.sp
    val textFontSize: TextUnit = 18.sp

    val uiState by connectionViewModel.uiState.collectAsState()
    val keyboardController = LocalSoftwareKeyboardController.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 5.dp)
            .clickable {
                keyboardController?.hide()
            },
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "DroneControl App",
            fontSize = titleFontSize,
            modifier = Modifier.padding(vertical = 16.dp)
        )
        Spacer(modifier = Modifier.height(30.dp))


        Button(
            onClick = { connectionViewModel.connect2Server() },
            modifier = Modifier.align(Alignment.CenterHorizontally),

            ) {
            Text("Start", fontSize = textFontSize)
        }

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = {  },
            modifier = Modifier.align(Alignment.CenterHorizontally),

            ) {
            Text("Saved videos", fontSize = textFontSize)
        }

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = {  },
            modifier = Modifier.align(Alignment.CenterHorizontally),

            ) {
            Text("Exit", fontSize = textFontSize)
        }

        Spacer(modifier = Modifier.height(8.dp))

        if (uiState.mainScreenErrorText != "")
        {
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = uiState.mainScreenErrorText,
                fontSize = textFontSize,
                color = Color.Red)
        }
    }
}