<template>
    <div id="avatar" :class="{ 'walking': direction !== 0, 'follow': follow_anim, 'follow_longer': follow_longer}">
        <div id="follow" :class="{'anim': follow_anim}">
            <div v-if="follow_anim" id="thanks">Thanks!</div>
            <div id="name_container"><span id="name">{{ props.data.display }}</span></div>
            <img id="pfp" :src="props.data.profile_image">
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';

let props = defineProps({
    data: Object
});

let x = ref(Math.random() * 100);
let y = ref(0);

let direction = ref(0);

setInterval(() => {
    x.value += direction.value * 0.1;
    if (x.value >= 100) {
        direction.value = -1;
    } else if (x.value <= 0) {
        direction.value = 1;
    }
}, 10);

function random_turn() {
    if (Math.random() > 0.5) {
        direction.value = Math.random() > 0.5 ? 1 : -1;
    } else {
        direction.value = 0;
    }

    setTimeout(random_turn, Math.random() * 5000 + 3000);
}
random_turn();

let follow_anim = ref(false);
let follow_longer = ref(false);
function follow() {
    direction.value = 0;
    follow_anim.value = true;
    follow_longer.value = true;
    setTimeout(() => {
        follow_anim.value = false;
        setTimeout(() => {
            follow_longer.value = false;
            x.value = 50;
        }, 1000);
    }, 5000);
}

defineExpose({
    follow
});
</script>

<style scoped>
#avatar {
    position: fixed;
    left: v-bind("x + '%'");
    bottom: v-bind("y + '%'");
    transform: translateX(-50%);
}

#name {
    font-size: 20px;

    text-align: center;
    margin-left: -100%;
    margin-right: -100%;
}

#name_container {
    width: 100px;
    white-space: nowrap;
    text-align: center;
}

#pfp {
    width: 100px;
    height: 100px;

}

#avatar.walking #pfp {
    animation: walking 0.5s ease-in-out infinite;
}

@keyframes walking {
    0% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-5px);
    }

    100% {
        transform: translateY(0);
    }
}

#avatar {
    animation: drop 2s linear forwards;
}

@keyframes drop {
    0% {
        transform: translateY(-1080px);
    }

    60% {
        transform: translateY(0);
    }
    70% {
        transform: translateY(-30px);
    }
    80% {
        transform: translateY(0);
    }
    90% {
        transform: translateY(-10px);
    }
    100% {
        transform: translateY(0);
    }
}

#avatar.follow_longer {
    transition: left 1s, bottom 1s;
    left: 50%;
    bottom: 0%;
}

#avatar.follow {
    left: 50%;
    bottom: 50%;
}

#follow.anim {
    animation: follow 5s linear forwards;
}
#follow.anim #pfp {
    animation: follow_pfp 1s linear infinite;
}

@keyframes follow {
    0% {
        transform: scale(1);
    }

    25% {
        transform: scale(4);
    }
    75% {
        transform: scale(4);
    }
    
    100% {
        transform: scale(1);
    }
}

/* Wobble */
@keyframes follow_pfp {
    0% {
        transform: rotate(0deg);
    }
    25% {
        transform: rotate(10deg);
    }
    50% {
        transform: rotate(0deg);
    }
    75% {
        transform: rotate(-10deg);
    }
    100% {
        transform: rotate(0deg);
    }
}

#thanks {
    font-size: 30px;
    animation: thanks 1s linear infinite;
}
@keyframes thanks {
    0% {
        color: #9400d3;
    }
    50% {
        color: #ff00ff;
    }
    100% {
        color: #9400d3;
    }
}
</style>
