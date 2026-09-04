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
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value))
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

  if (loading && !feed) return <Status>Loading Playground…</Status>
  if (error && !feed) return <Status>콘텐츠를 불러오지 못했습니다.</Status>

  if (selected) {
    return (
      <article className="w-full bg-white text-black">
        <div className="mx-auto max-w-[760px] px-4 md:px-8 py-12 md:py-24">
          <button
            type="button"
            onClick={() => setSelected(null)}
            className="mb-16 text-[13px] text-[#313131] font-['Source_Code_Pro'] bg-transparent border-0 p-0 cursor-pointer"
          >
            ← Playground
          </button>

          <div className="text-[12px] leading-none text-[#021f6f] font-['Source_Code_Pro'] font-medium uppercase">
            Article
          </div>
          <h1 className="mt-5 text-[36px] md:text-[54px] leading-[1.14] font-['Pretendard'] font-medium tracking-[-0.025em]">
            {selected.title}
          </h1>
          <time className="block mt-6 text-[12px] text-[#6a6a6a] font-['Source_Code_Pro']">
            {dateLabel(selected.date)}
          </time>

          {selected.thumbnail && (
            <img
              src={selected.thumbnail}
              alt=""
              className="block w-full mt-12 object-cover"
            />
          )}

          <div className="mt-12 font-['Pretendard']">
            {selected.contentBlocks?.length ? selected.contentBlocks.map((block, index) => {
              if (block.type === "image") {
                return (
                  <figure key={`${block.url}-${index}`} className="my-12">
                    <img src={block.url} alt={block.alt ?? ""} className="block w-full h-auto" />
                    {block.caption && (
                      <figcaption className="mt-3 text-center text-[12px] leading-[1.5] text-[#777]">
                        {block.caption}
                      </figcaption>
                    )}
                  </figure>
                )
              }
              if (block.style === "heading2") return <h2 key={index} className="mt-16 mb-5 text-[28px] leading-[1.35] font-semibold">{block.text}</h2>
              if (block.style === "heading3") return <h3 key={index} className="mt-12 mb-4 text-[22px] leading-[1.45] font-semibold">{block.text}</h3>
              if (block.style === "quote") return <blockquote key={index} className="my-8 border-l-2 border-[#021f6f] pl-5 text-[17px] leading-[1.9] whitespace-pre-line">{block.text}</blockquote>
              return <p key={index} className="my-5 text-[17px] leading-[1.9] whitespace-pre-line">{block.text}</p>
            }) : (
              <p className="text-[17px] leading-[1.9] whitespace-pre-wrap">{selected.content}</p>
            )}
          </div>

          <a
            href={selected.originalUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-block mt-16 text-[13px] text-[#021f6f] underline underline-offset-4 font-['Source_Code_Pro']"
          >
            브런치에서 원문 보기 ↗
          </a>
        </div>
      </article>
    )
  }

  return (
    <section className="w-full bg-white text-black">
      <div className="mx-auto w-full px-4 md:px-8 py-12 md:py-20">
        <div className="flex flex-wrap gap-x-6 gap-y-3 mb-10 text-[13px] font-['Source_Code_Pro']">
          <span className="text-black">All</span>
          <span className="text-[#021f6f]">Article</span>
          <span className="text-[#8a8a8a]">AI Experiment</span>
          <span className="text-[#8a8a8a]">Graphic</span>
          <span className="text-[#8a8a8a]">Interaction</span>
          <span className="text-[#8a8a8a]">Side Project</span>
        </div>

        <div className="border-t border-[#dedede]">
          {feed?.items.map((article) => (
            <button
              key={article.id}
              type="button"
              onClick={() => openArticle(article)}
              className="group flex w-full min-h-[252px] items-stretch justify-between gap-10 text-left bg-transparent border-0 border-b border-solid border-[#dedede] px-0 py-8 cursor-pointer"
            >
              <div className="flex min-w-0 flex-1 flex-col py-1">
                <span className="text-[12px] leading-none text-[#021f6f] font-['Source_Code_Pro'] font-medium">
                  Article
                </span>
                <h2 className="mt-3 text-[22px] leading-[1.25] font-['Pretendard'] font-medium tracking-[-0.015em]">
                  {article.title}
                </h2>
                <p className="mt-3 text-[14px] leading-[1.65] text-[#6a6a6a] font-['Pretendard'] line-clamp-3">
                  {article.description}
                </p>
                <time className="mt-auto pt-8 text-[12px] leading-none text-[#6a6a6a] font-['Source_Code_Pro']">
                  {dateLabel(article.date)}
                </time>
              </div>
              <div className="w-[30%] min-w-[220px] max-w-[320px] overflow-hidden bg-[#f3f3f3]">
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
