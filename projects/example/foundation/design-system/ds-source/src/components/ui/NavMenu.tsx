import * as React from "react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

export type NavMenuItem = {
  /** 메뉴 라벨 (예: 프로젝트 관리) */
  label: string
  /** 이동 경로 */
  href?: string
  /** 현재 활성 메뉴 여부 */
  active?: boolean
  /** 클릭 핸들러 (href 없이 동작시) */
  onSelect?: () => void
}

export interface NavMenuProps extends React.ComponentProps<"nav"> {
  items: NavMenuItem[]
}

/**
 * NavMenu — 상단 글로벌 헤더의 가로 대메뉴.
 * shadcn 기본 컴포넌트(Button, variant=ghost/link) 위에 만든 프로젝트 합성 컴포넌트.
 * 별도 NavigationMenu primitive를 쓰지 않고 Button 링크 묶음으로 단순화한다.
 */
function NavMenu({ items, className, ...props }: NavMenuProps) {
  return (
    <nav
      data-slot="nav-menu"
      aria-label="main"
      className={cn("flex items-center gap-1", className)}
      {...props}
    >
      {items.map((item) => (
        <Button
          key={item.label}
          asChild={!!item.href}
          variant="ghost"
          size="sm"
          data-active={item.active || undefined}
          onClick={item.onSelect}
          className={cn(
            "text-muted-foreground data-[active]:text-foreground data-[active]:bg-accent font-medium"
          )}
        >
          {item.href ? <a href={item.href}>{item.label}</a> : <span>{item.label}</span>}
        </Button>
      ))}
    </nav>
  )
}

export { NavMenu }
