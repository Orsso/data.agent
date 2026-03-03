'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { cn } from '@/lib/utils'

interface BrandLogoProps {
  size?: 'sm' | 'lg'
  href?: string
  expanded?: boolean
  animateOnMount?: boolean
}

export function BrandLogo({ size = 'sm', href, expanded = false, animateOnMount = false }: BrandLogoProps) {
  const lg = size === 'lg'

  const [open, setOpen] = useState(animateOnMount ? false : expanded)

  useEffect(() => {
    if (!animateOnMount) return
    const id = requestAnimationFrame(() => setOpen(true))
    return () => cancelAnimationFrame(id)
  }, [animateOnMount])

  const content = (
    <>
      <div className={cn(
        'shrink-0 rounded-[1px] bg-[#6DA5FF] transition-transform duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]',
        lg ? 'w-[5px] h-[36px]' : 'w-[4px] h-[26px]',
        open
          ? (lg ? '-translate-x-[4px]' : '-translate-x-[3px]')
          : (lg ? 'group-hover:-translate-x-[4px]' : 'group-hover:-translate-x-[3px]'),
      )} />
      <div className={cn(
        'overflow-hidden transition-[max-width] duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]',
        open
          ? (lg ? 'max-w-[14rem]' : 'max-w-[8.5rem]')
          : (lg ? 'max-w-[7px] group-hover:max-w-[14rem]' : 'max-w-[6px] group-hover:max-w-[8.5rem]'),
      )}>
        <span className={cn(
          'flex items-center whitespace-nowrap font-everett font-semibold tracking-tight text-foreground transition-opacity duration-500 delay-200 ease-out',
          lg ? 'h-12 px-4 text-3xl font-bold' : 'h-9 px-3 text-base',
          open ? 'opacity-100' : 'opacity-0 group-hover:opacity-100',
        )}>
          data.agent
        </span>
      </div>
      <div className={cn(
        'shrink-0 self-start rounded-[1px] bg-[#6DA5FF] transition-transform duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]',
        lg ? 'w-[5px] h-[36px]' : 'w-[4px] h-[26px]',
        open
          ? (lg ? 'translate-x-[4px]' : 'translate-x-[3px]')
          : (lg ? 'group-hover:translate-x-[4px]' : 'group-hover:translate-x-[3px]'),
      )} />
    </>
  )

  const className = cn('group flex items-end select-none', lg ? 'h-12' : 'h-9')

  if (href) {
    return <Link href={href} className={className}>{content}</Link>
  }
  return <div className={className}>{content}</div>
}
