<template>
    <div id="page">
        <!-- <div id="alert"></div> -->

        <div id="wallpaper-name">
            <WallpaperName :name="wallpaper_author" />
        </div>

        <StreamAvatars ref="stream_avatars" />
    </div>
</template>

<script setup>
import WallpaperName from '@/components/WallpaperName.vue';
import StreamAvatars from '@/components/StreamAvatars.vue';

import { ref } from 'vue';

let wallpaper_author = ref('Unknown');

let stream_avatars = ref(null);

const socket = new WebSocket('ws://localhost:8000');
socket.onmessage = (event) => {
    event = JSON.parse(event.data);
    if (event.type === 'wallpaper') {
        wallpaper_author.value = event.data;
    } else if (event.type === 'add_name') {
        stream_avatars.value.add_name(event.data);
    } else if (event.type === 'update_pfp') {
        stream_avatars.value.update_pfp(event.data);
    } else if (event.type === 'follow') {
        stream_avatars.value.add_name(event.data);
        stream_avatars.value.follow(event.data);
    } else if (event.type === 'raid') {
        // Classic popup
        // Some sort of game
        // 
    }
}
</script>

<style scoped>
#page {
    height: 100vh;
    width: 100vw;
}

#wallpaper-name {
    position: fixed;
    right: 0;
}

#alert {
    width: 300px;
    height: 300px;
    background-color: red;

    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}
</style>

