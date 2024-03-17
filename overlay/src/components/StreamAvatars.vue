<template>
    <template v-for="avatar in avatars" :key="avatar.name">
        <Avatar :data="avatar" :ref="(el) => {console.log(el); avatar_elms[avatar.name] = el}" />
    </template>
</template>

<script setup>
import Avatar from '@/components/Avatar.vue';

import { ref } from 'vue';

let avatars = ref({
});
let avatar_elms = ref({});

function add_name(data) {
    if (!avatars.value[data.name]) avatars.value[data.name] = data;
}
function update_pfp(data) {
    avatars.value[data.name].profile_image = data.profile_image;
}

function get_elm(name) {
    console.log(avatar_elms.value);
    return avatar_elms.value[name];
}

let follow_sound = new Audio('/follow.mp3');

function follow(data) {
    follow_sound.play();
    let elm = get_elm(data.name);
    elm.follow();
}

defineExpose({
    add_name,
    update_pfp,
    follow
});
</script>
