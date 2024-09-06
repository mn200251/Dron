package com.example.dronecontrol.screens

import android.content.Intent
import android.os.Build
import androidx.annotation.RequiresApi
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.zIndex
import com.example.dronecontrol.R
import com.example.dronecontrol.models.VideoItem
import com.example.dronecontrol.services.DownloadService
import com.example.dronecontrol.sharedRepositories.SharedRepository
import com.example.dronecontrol.viewmodels.SCREEN
import com.example.dronecontrol.viewmodels.VideoViewModel

@RequiresApi(Build.VERSION_CODES.O)
@Composable
fun VideoListScreen(viewModel: VideoViewModel ) {
    val videoState by viewModel.videoState.collectAsState()
    val context = LocalContext.current

    val buttonSize = 60.dp

    LaunchedEffect(Unit) {
        viewModel.fetchVideos()
    }

    Box(
        modifier = Modifier.fillMaxSize(),
    ) {
        IconButton(
            onClick = {
                /*TODO*/
                SharedRepository.setScreen(SCREEN.MainScreen)
            },
            modifier = Modifier
                .align(Alignment.TopStart)
                .padding(start = 14.dp, top = 14.dp)
                .size(buttonSize)
                .zIndex(1f)
        ) {
            Icon(
                painter = painterResource(id = R.drawable.exit_icon),
                contentDescription = "Exit Button Icon",
                tint = Color(64, 64, 64, 75),
            )
        }
        Column(
            modifier=Modifier
                .fillMaxSize()
                .align(Alignment.Center)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            videoState.videos.forEach{ video ->
                VideoItem(video = video,onDownloadConfirm = { video ->
                    val intent = Intent(context, DownloadService::class.java).apply {
                        action = "ACTION_APP_FOREGROUND" // This can be customized as needed
                        putExtra("videoName", video.filename)
                    }
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        context.startForegroundService(intent)
                    } else {
                        context.startService(intent)
                    }
                })
            }
        }
    }
}
