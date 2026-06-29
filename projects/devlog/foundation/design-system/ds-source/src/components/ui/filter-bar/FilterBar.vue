<script setup lang="ts">
import { computed } from 'vue'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Search } from 'lucide-vue-next'

interface TagOption {
  label: string
  value: string
}

interface SortOption {
  label: string
  value: string
}

interface FilterState {
  search: string
  tag: string
  sort: string
}

const props = withDefaults(defineProps<{
  tags?: TagOption[]
  sortOptions?: SortOption[]
  modelValue?: FilterState
}>(), {
  tags: () => [],
  sortOptions: () => [
    { label: '최신순', value: 'latest' },
    { label: '인기순', value: 'popular' },
    { label: '오래된순', value: 'oldest' },
  ],
  modelValue: () => ({ search: '', tag: '', sort: 'latest' }),
})

const emit = defineEmits<{
  'update:modelValue': [value: FilterState]
  search: [value: string]
}>()

const state = computed({
  get: () => props.modelValue ?? { search: '', tag: '', sort: 'latest' },
  set: (val) => emit('update:modelValue', val),
})

function onSearch(e: Event) {
  const val = (e.target as HTMLInputElement).value
  state.value = { ...state.value, search: val }
  emit('search', val)
}

function selectTag(tag: string) {
  state.value = { ...state.value, tag: state.value.tag === tag ? '' : tag }
}

function onSort(val: string) {
  state.value = { ...state.value, sort: val }
}
</script>

<template>
  <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
    <!-- 검색 -->
    <div class="relative flex-1">
      <Search class="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
      <Input
        :value="state.search"
        placeholder="검색..."
        class="pl-9"
        @input="onSearch"
      />
    </div>

    <!-- 태그 필터 -->
    <div v-if="tags.length" class="flex flex-wrap gap-1">
      <Button
        v-for="tag in tags"
        :key="tag.value"
        variant="outline"
        size="sm"
        :class="state.tag === tag.value ? 'border-primary text-primary bg-primary/10' : ''"
        @click="selectTag(tag.value)"
      >
        {{ tag.label }}
      </Button>
    </div>

    <!-- 정렬 -->
    <Select :model-value="state.sort" @update:model-value="onSort">
      <SelectTrigger class="w-28 shrink-0">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem
          v-for="opt in sortOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </SelectItem>
      </SelectContent>
    </Select>
  </div>
</template>
