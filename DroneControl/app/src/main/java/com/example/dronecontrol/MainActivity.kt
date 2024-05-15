package com.example.dronecontrol

import android.os.Bundle
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
import com.example.dronecontrol.ui.theme.DroneControlTheme

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
    MainScreen()


}

@OptIn(ExperimentalComposeUiApi::class)
@Composable
fun MainScreen() {
    val inputFieldWidth: Dp = 500.dp
    val titleFontSize: TextUnit = 30.sp
    val textFontSize: TextUnit = 18.sp
    var errorText by remember { mutableStateOf<String>("") }

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
        TextField(
            value = "",
            onValueChange = {},
            label = { Text(
                "IP Address",
                fontSize = textFontSize
                ) },
            modifier = Modifier.width(inputFieldWidth)
        )
        Spacer(modifier = Modifier.height(16.dp))
        TextField(
            value = "",
            onValueChange = {},
            label = { Text(
                "Port",
                fontSize = textFontSize
                ) },
            modifier = Modifier.width(inputFieldWidth),
            keyboardOptions = KeyboardOptions.Default.copy(keyboardType = KeyboardType.Number),
        )

        if (errorText != "")
        {
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = errorText,
                fontSize = textFontSize,
                color = Color.Red)
        }

        Spacer(modifier = Modifier.height(16.dp))
        Button(
            onClick = { /* Connect button clicked */ },
            modifier = Modifier.align(Alignment.CenterHorizontally)
        ) {
            Text("Connect", fontSize = textFontSize)
        }
    }
}


@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}

@Preview(showBackground = true)
@Composable
fun GreetingPreview() {
    DroneControlTheme {
        Greeting("Android")
    }
}