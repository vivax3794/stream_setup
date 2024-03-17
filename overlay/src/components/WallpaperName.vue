<template>
    <div id="wallpaper-name">
        <p>
            Wallpaper by:
            <span>{{ props.name }}</span>
        </p>
    </div>
</template>

<script setup>
let props = defineProps({
    name: String
});
</script>

<style scoped>
#wallpaper-name {
    margin-top: 50px;
    margin-right: 50px;
}

p {
    font-size: 40px;
}
</style>
