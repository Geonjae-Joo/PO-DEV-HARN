<script setup lang="ts">
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { Sun, Moon, LogOut, User, Menu } from 'lucide-vue-next'

interface NavItem {
  label: string
  href: string
  active?: boolean
}

interface AuthUser {
  name: string
  email?: string
  avatarUrl?: string
}

const props = withDefaults(defineProps<{
  brand?: string
  navItems?: NavItem[]
  user?: AuthUser | null
  isDark?: boolean
}>(), {
  brand: 'DevLog',
  navItems: () => [],
  user: null,
  isDark: false,
})

const emit = defineEmits<{
  'toggle-theme': []
  login: []
  logout: []
  nav: [href: string]
}>()

function initials(name: string) {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}
</script>

<template>
  <header class="sticky top-0 z-40 w-full border-b border-border bg-background/80 backdrop-blur-sm">
    <div class="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4">
      <!-- Brand -->
      <span class="text-lg font-bold text-primary shrink-0">{{ brand }}</span>

      <!-- Nav Items -->
      <nav v-if="navItems.length" class="hidden md:flex items-center gap-1">
        <Separator orientation="vertical" class="mx-1 h-5" />
        <Button
          v-for="item in navItems"
          :key="item.href"
          variant="ghost"
          size="sm"
          :class="item.active ? 'text-primary' : 'text-muted-foreground'"
          @click="emit('nav', item.href)"
        >
          {{ item.label }}
        </Button>
      </nav>

      <div class="flex-1" />

      <!-- Theme Toggle -->
      <Button variant="ghost" size="icon" @click="emit('toggle-theme')">
        <Sun v-if="isDark" class="size-4" />
        <Moon v-else class="size-4" />
      </Button>

      <!-- Auth: logged in -->
      <DropdownMenu v-if="user">
        <DropdownMenuTrigger as-child>
          <Button variant="ghost" class="h-8 w-8 rounded-full p-0">
            <Avatar class="size-8">
              <AvatarImage :src="user.avatarUrl ?? ''" :alt="user.name" />
              <AvatarFallback>{{ initials(user.name) }}</AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" class="w-48">
          <div class="px-2 py-1.5 text-sm font-medium">{{ user.name }}</div>
          <div v-if="user.email" class="px-2 pb-1 text-xs text-muted-foreground">{{ user.email }}</div>
          <DropdownMenuSeparator />
          <DropdownMenuItem @select="emit('nav', '/profile')">
            <User class="mr-2 size-4" /> 프로필
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem class="text-destructive" @select="emit('logout')">
            <LogOut class="mr-2 size-4" /> 로그아웃
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <!-- Auth: guest -->
      <Button v-else size="sm" @click="emit('login')">로그인</Button>

      <!-- Mobile menu slot -->
      <Button variant="ghost" size="icon" class="md:hidden">
        <Menu class="size-4" />
      </Button>
    </div>
  </header>
</template>
