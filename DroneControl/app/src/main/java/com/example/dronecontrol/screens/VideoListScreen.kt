package com.example.dronecontrol.screens

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import com.example.dronecontrol.models.VideoItem
import com.example.dronecontrol.viewmodels.VideoViewModel

@Composable
fun VideoListScreen(viewModel: VideoViewModel ) {
    val videoState by viewModel.videoState.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.fetchVideos()
    }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        LazyColumn {
            items(videoState.videos) { video ->
                VideoItem(video = video)
            }
        }
    }
}
