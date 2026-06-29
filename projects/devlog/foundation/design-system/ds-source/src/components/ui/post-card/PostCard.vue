<script setup lang="ts">
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Heart } from 'lucide-vue-next'

interface Post {
  id: string | number
  title: string
  summary?: string
  tags?: string[]
  author?: string
  date?: string
  thumbnailUrl?: string
}

const props = withDefaults(defineProps<{
  post: Post
  liked?: boolean
  likeCount?: number
}>(), {
  liked: false,
  likeCount: 0,
})

const emit = defineEmits<{
  like: [id: string | number]
  click: [id: string | number]
}>()
</script>

<template>
  <Card
    class="group flex flex-col overflow-hidden transition-shadow hover:shadow-md cursor-pointer"
    @click="emit('click', post.id)"
  >
    <!-- Thumbnail -->
    <div v-if="post.thumbnailUrl" class="aspect-video w-full overflow-hidden">
      <img
        :src="post.thumbnailUrl"
        :alt="post.title"
        class="h-full w-full object-cover transition-transform group-hover:scale-105"
      />
    </div>

    <CardHeader class="pb-2">
      <!-- Tags -->
      <div v-if="post.tags?.length" class="flex flex-wrap gap-1 mb-2">
        <Badge
          v-for="tag in post.tags"
          :key="tag"
          variant="secondary"
          class="text-xs"
        >
          {{ tag }}
        </Badge>
      </div>
      <CardTitle class="line-clamp-2 text-base leading-snug">{{ post.title }}</CardTitle>
    </CardHeader>

    <CardContent class="flex-1 pb-2">
      <p v-if="post.summary" class="text-sm text-muted-foreground line-clamp-2">
        {{ post.summary }}
      </p>
    </CardContent>

    <CardFooter class="flex items-center justify-between pt-2">
      <div class="flex items-center gap-1 text-xs text-muted-foreground">
        <span v-if="post.author">{{ post.author }}</span>
        <span v-if="post.author && post.date">·</span>
        <span v-if="post.date">{{ post.date }}</span>
      </div>

      <Button
        variant="ghost"
        size="sm"
        class="h-7 gap-1 px-2"
        :class="liked ? 'text-primary' : 'text-muted-foreground'"
        @click.stop="emit('like', post.id)"
      >
        <Heart class="size-3.5" :fill="liked ? 'currentColor' : 'none'" />
        <span class="text-xs">{{ likeCount }}</span>
      </Button>
    </CardFooter>
  </Card>
</template>
