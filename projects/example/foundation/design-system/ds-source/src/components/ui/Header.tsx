import * as React from "react"

import { cn } from "@/lib/utils"
import { NavMenu, type NavMenuItem } from "@/components/ui/NavMenu"

export interface HeaderProps extends React.ComponentProps<"header"> {
  /** 좌측 끝 시스템명/브랜드 (예: PO-DEV-CHAT for SENA) */
  brand: React.ReactNode
  /** 가운데 대메뉴 항목 */
  menu?: NavMenuItem[]
  /** 우측 끝 액션 영역 (예: Avatar, DropdownMenu) */
  actions?: React.ReactNode
}

/**
 * Header — 전체 페이지 상단 글로벌 헤더 셸.
 * 좌(브랜드) · 중(NavMenu 대메뉴) · 우(actions) 3분할 합성 컴포넌트.
 * NavMenu(프로젝트 합성) + 임의 actions 슬롯(Avatar/DropdownMenu 권장)으로 구성된다.
 */
function Header({ brand, menu, actions, className, ...props }: HeaderProps) {
  return (
    <header
      data-slot="header"
      className={cn(
        "bg-background sticky top-0 z-40 flex h-14 w-full items-center gap-4 border-b px-4",
        className
      )}
      {...props}
    >
      <div data-slot="header-brand" className="flex items-center font-semibold">
        {brand}
      </div>
      <div data-slot="header-nav" className="flex flex-1 items-center justify-center">
        {menu ? <NavMenu items={menu} /> : null}
      </div>
      <div data-slot="header-actions" className="flex items-center gap-2">
        {actions}
      </div>
    </header>
  )
}

export { Header }
