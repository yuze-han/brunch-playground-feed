import React, { useEffect, useState } from "react"

const FEED_BASE = typeof window !== "undefined" && window.location.hostname === "127.0.0.1"
  ? "/data"
  : "https://raw.githubusercontent.com/yuze-han/brunch-playground-feed/main/data"

type Source = {
  provider: "brunch"
  guid: string
  fingerprint: string
  dateModified?: string
}

type ArticleCard = {
  id: string
  type: "article"
  title: string
  description: string
  date: string
  thumbnail: string | null
  tags?: string[]
  originalUrl: string
  slug: string
  source: Source
}

type ArticleDetail = ArticleCard & {
  content: string
  contentFormat: "text"
  contentBlocks?: Array<
    | { type: "text"; style: "paragraph" | "heading2" | "heading3" | "quote"; text: string }
    | { type: "image"; url: string; width?: number; height?: number; alt?: string; caption?: string }
  >
  images: Array<{ url: string; width?: number; height?: number; alt?: string }>
}

type Feed = {
  schemaVersion: number
  generatedAt: string
  items: ArticleCard[]
}

function dateLabel(value: string) {
  const parts = new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: "Asia/Seoul",
  }).formatToParts(new Date(value))
  const read = (type: Intl.DateTimeFormatPartTypes) => parts.find((part) => part.type === type)?.value
  return `${read("year")}/${read("month")}/${read("day")}`
}

function Status({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-[320px] flex items-center justify-center text-[13px] text-[#6a6a6a] font-['Source_Code_Pro']">
      {children}
    </div>
  )
}

export default function Playground() {
  const [feed, setFeed] = useState<Feed | null>(null)
  const [selected, setSelected] = useState<ArticleDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let active = true
    fetch(`${FEED_BASE}/index.json`)
      .then((response) => {
        if (!response.ok) throw new Error(`Feed request failed: ${response.status}`)
        return response.json()
      })
      .then((value: Feed) => active && setFeed(value))
      .catch(() => active && setError(true))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  async function openArticle(card: ArticleCard) {
    setLoading(true)
    setError(false)
    try {
      const response = await fetch(`${FEED_BASE}/articles/${card.slug}.json`)
      if (!response.ok) throw new Error(`Article request failed: ${response.status}`)
      setSelected(await response.json())
      window.scrollTo({ top: 0, behavior: "smooth" })
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  const nextArticle = selected && feed
    ? feed.items[feed.items.findIndex((item) => item.id === selected.id) + 1]
    : undefined

  if (loading && !feed) return <Status>Loading Playground…</Status>
  if (error && !feed) return <Status>콘텐츠를 불러오지 못했습니다.</Status>

  if (selected) {
    return (
      <article className="w-full bg-white text-black">
        <div className="mx-auto w-full max-w-[1030px] px-[40px]">
          {selected.thumbnail && (
            <img
              src={selected.thumbnail}
              alt=""
              className="block h-[261px] w-full object-cover"
            />
          )}

          <header className="flex flex-col items-start gap-[24px] pb-[60px] pt-[40px]">
            <div className="text-[16px] font-medium leading-[1.03] tracking-[-0.045em] text-[#021f6f] underline font-['Source_Code_Pro']">
              {selected.tags?.[0] ?? "Article"}
            </div>
            <h1 className="w-full text-[40px] font-light leading-[1.1] tracking-[-0.01em] font-['Pretendard']">
              {selected.title}
            </h1>
            <div className="w-full pr-[32px] pb-[20px]">
              <p className="text-[15px] leading-[1.4] text-[#575757] font-['Pretendard']">
                {selected.description}
              </p>
              <time className="mt-[12px] block text-[13px] leading-[1.03] text-[#575757] font-['Source_Code_Pro']">
                {dateLabel(selected.date)}
              </time>
            </div>
          </header>

          <div className="font-['Pretendard']">
            {selected.contentBlocks?.length ? selected.contentBlocks.map((block, index) => {
              if (block.type === "image") {
                return (
                  <figure key={`${block.url}-${index}`} className="m-0 pr-[32px] pt-[60px]">
                    <img src={block.url} alt={block.alt ?? ""} className="block h-auto w-full object-contain" />
                    {block.caption && (
                      <figcaption className="mt-[12px] w-full text-center text-[15px] leading-[1.4] text-[#575757]">
                        {block.caption}
                      </figcaption>
                    )}
                  </figure>
                )
              }
              if (block.style === "heading2") return <h2 key={index} className="w-full pt-[40px] text-[30px] font-medium leading-[1.4] tracking-[-0.02em]">{block.text}</h2>
              if (block.style === "heading3") return <h3 key={index} className="w-full pt-[40px] text-[22px] font-medium leading-[1.4] tracking-[-0.02em]">{block.text}</h3>
              if (block.style === "quote") return <div key={index} className="mt-[40px] border border-[rgba(0,0,0,0.1)] px-[30px] py-[40px] text-[15px] leading-[1.4] text-[#575757] whitespace-pre-line">{block.text}</div>
              return <p key={index} className="mt-[20px] text-[15px] leading-[1.4] text-[#575757] whitespace-pre-line">{block.text}</p>
            }) : (
              <p className="text-[15px] leading-[1.4] text-[#575757] whitespace-pre-wrap">{selected.content}</p>
            )}
          </div>

          <div className="flex items-center gap-[12px] py-[64px] font-['Source_Code_Pro'] text-[15px] leading-[1.2]">
            <button type="button" onClick={() => setSelected(null)} className="cursor-pointer border border-black bg-white px-[8px] py-[6px]">
              ← Playground
            </button>
            {nextArticle && (
              <button type="button" onClick={() => openArticle(nextArticle)} className="cursor-pointer border border-black bg-white px-[8px] py-[6px]">
                다음 글 보기 →
              </button>
            )}
            <a href={selected.originalUrl} target="_blank" rel="noreferrer" className="border border-black px-[8px] py-[6px] text-black no-underline">
              브런치 원문 ↗
            </a>
          </div>
        </div>
      </article>
    )
  }

  return (
    <section className="w-full bg-white text-black">
      <div className="mx-auto w-full max-w-[1030px] px-[40px] py-[40px]">
        <p className="pb-[20px] text-[15px] leading-[1.4] text-[#575757] font-['Pretendard']">
          {feed?.items.length ?? 0}개의 글
        </p>

        <div>
          {feed?.items.map((article) => (
            <button
              key={article.id}
              type="button"
              onClick={() => openArticle(article)}
              className="group flex w-full min-h-[324px] items-stretch justify-between gap-[60px] border-0 border-t-[0.75px] border-solid border-[#4f4f4f] bg-transparent px-0 py-[32px] text-left cursor-pointer"
            >
              <div className="flex min-w-0 flex-1 flex-col py-1">
                <span className="text-[16px] font-medium leading-[1.03] tracking-[-0.045em] text-[#021f6f] underline font-['Source_Code_Pro']">
                  {article.tags?.[0] ?? "Article"}
                </span>
                <h2 className="mt-[16px] text-[30px] font-medium leading-[1.4] tracking-[-0.02em] font-['Pretendard']">
                  {article.title}
                </h2>
                <p className="mt-[16px] text-[15px] leading-[1.4] text-[#575757] font-['Pretendard'] line-clamp-3">
                  {article.description}
                </p>
                <time className="mt-auto pt-[20px] text-[16px] leading-[1.03] tracking-[-0.045em] text-[#575757] font-['Source_Code_Pro']">
                  {dateLabel(article.date)}
                </time>
              </div>
              <div className="size-[260px] shrink-0 overflow-hidden bg-[#f3f3f3]">
                {article.thumbnail && (
                  <img
                    src={article.thumbnail}
                    alt=""
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.02]"
                  />
                )}
              </div>
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
