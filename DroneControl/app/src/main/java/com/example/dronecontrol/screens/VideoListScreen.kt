package com.example.dronecontrol.screens

import android.content.Intent
import android.os.Build
import android.widget.Toast
import androidx.annotation.RequiresApi
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
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
import androidx.compose.ui.unit.sp
import androidx.compose.ui.zIndex
import com.example.dronecontrol.R
import com.example.dronecontrol.models.VideoItem
import com.example.dronecontrol.services.DownloadService
import com.example.dronecontrol.sharedRepositories.SharedRepository
import com.example.dronecontrol.viewmodels.SCREEN
import com.example.dronecontrol.viewmodels.VideoViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext

@RequiresApi(Build.VERSION_CODES.O)
@Composable
fun VideoListScreen(viewModel: VideoViewModel ) {
    val videoState by viewModel.videoState.collectAsState()
    val context = LocalContext.current

    val buttonSize = 60.dp

    LaunchedEffect(Unit) {
        viewModel.fetchVideos()

        // viewModel.setRefresh(false)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black) // Set black background
            .padding(16.dp)
    ) {
        // Exit Button
        OutlinedButton(
            onClick = { SharedRepository.setScreen(SCREEN.MainScreen) },
            modifier = Modifier
                .align(Alignment.Start)
                .padding(bottom = 16.dp)
        ) {
            Text(text = "Exit", color = Color.White)
        }

        if (videoState.isLoading) {
            // Show Loading Spinner
            Box(
                modifier = Modifier
                    .fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = Color.White)
            }
        }
        else if(videoState.videos.isEmpty())
        {
            Box(
                modifier = Modifier
                    .fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Text(text = "No Videos Available", color = Color.White, fontSize = 25.sp)
            }
        }
        else
        {
            // List of Videos in LazyColumn
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                items(videoState.videos) { video ->
                    VideoItem(video = video, onDownloadConfirm = { selectedVideo ->
                        // Trigger download action
                        val intent = Intent(context, DownloadService::class.java).apply {
                            action = "ACTION_APP_FOREGROUND"
                            putExtra("videoName", selectedVideo.filename)
                        }
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            context.startForegroundService(intent)
                        } else {
                            context.startService(intent)
                        }
                    },
                        onDeleteConfirm = { deletedVideo ->
                            viewModel.deleteVideo(deletedVideo.filename)

                            val toast = Toast(context)
                            toast.setText("Deleted video")
                            toast.show()

                            viewModel.fetchVideos(1200)
                                          },
                        onRenameConfirm = { oldName, newName ->
                            viewModel.renameVideo(oldName = oldName, newName = newName)

                            val toast = Toast(context)
                            toast.setText("Renamed video")
                            toast.show()

                            viewModel.fetchVideos(1200)
                        }
                    )
                }
            }
        }
    }
}
