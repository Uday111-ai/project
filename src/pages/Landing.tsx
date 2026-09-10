import { Link } from "react-router-dom";

// Transcript content is real copy for the hero's signature visual — not decoration.
// This is the "one characteristic thing" from the subject's world: a live interview exchange.
const transcript = [
  { speaker: "ai", text: "Tell me about a time you disagreed with a decision at work." },
  {
    speaker: "user",
    text: "I pushed back on a launch timeline once — turned out the extra week saved us from a bad release.",
  },
  { speaker: "ai", text: "Good. What would you do differently if you had that time again?" },
];

const rounds = [
  {
    n: "01",
    title: "Mock interview",
    body: "Talk through real questions with an AI interviewer that adapts to your answers, not a script.",
  },
  {
    n: "02",
    title: "Instant feedback",
    body: "See exactly where an answer ran long, went vague, or missed the actual question asked.",
  },
  {
    n: "03",
    title: "Track growth",
    body: "Every session is saved, so you can watch your answers get sharper across attempts.",
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#10241F] text-[#F3EFE3]">
      {/* ---------------- NAV ---------------- */}
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6 md:px-10">
        <span className="font-[var(--font-display)] text-lg tracking-tight">Rehearsal</span>
        <nav className="flex items-center gap-6 text-sm">
          <Link to="/login" className="text-[#F3EFE3]/80 transition hover:text-[#F3EFE3]">
            Log in
          </Link>
          <Link
            to="/signup"
            className="rounded-full bg-[#C9A24B] px-4 py-2 font-medium text-[#10241F] transition hover:bg-[#dab566]"
          >
            Start practicing
          </Link>
        </nav>
      </header>

      {/* ---------------- HERO ---------------- */}
      <section className="mx-auto grid max-w-6xl gap-14 px-6 pb-20 pt-10 md:grid-cols-[1.1fr_0.9fr] md:gap-10 md:px-10 md:pt-16">
        {/* Left: headline */}
        <div className="flex flex-col justify-center">
          <h1 className="font-[var(--font-display)] text-[2.75rem] leading-[1.08] tracking-tight md:text-[3.4rem]">
            Practice the interview
            <br />
            before it practices you.
          </h1>
          <p className="mt-6 max-w-md text-[15px] leading-relaxed text-[#F3EFE3]/75">
            Rehearsal runs you through real interview questions, listens to how you actually answer, and
            tells you what to fix — before the interview that counts.
          </p>
          <div className="mt-9 flex items-center gap-5">
            <Link
              to="/signup"
              className="rounded-full bg-[#C9A24B] px-6 py-3 text-sm font-medium text-[#10241F] transition hover:bg-[#dab566]"
            >
              Start practicing free
            </Link>
            <a href="#how-it-works" className="text-sm text-[#F3EFE3]/70 underline decoration-[#3D6E5F] underline-offset-4 hover:text-[#F3EFE3]">
              How it works
            </a>
          </div>
        </div>

        {/* Right: the live transcript — signature visual */}
        <div className="rounded-2xl border border-[#3D6E5F]/40 bg-[#0B1512] p-6 shadow-2xl shadow-black/30">
          <div className="mb-4 flex items-center gap-2 text-xs text-[#F3EFE3]/40">
            <span className="h-2 w-2 rounded-full bg-[#C9A24B]" />
            Live session
          </div>
          <div className="space-y-4">
            {transcript.map((line, i) => (
              <div
                key={i}
                className="transcript-line"
                style={{ animationDelay: `${i * 0.6 + 0.2}s` }}
              >
                <p className="mb-1 text-[10px] uppercase tracking-wide text-[#3D6E5F]">
                  {line.speaker === "ai" ? "AI Interviewer" : "You"}
                </p>
                <p
                  className={
                    line.speaker === "ai"
                      ? "font-[var(--font-mono-ai)] text-[13.5px] leading-relaxed text-[#F3EFE3]/90"
                      : "text-[14px] leading-relaxed text-[#F3EFE3]"
                  }
                >
                  {line.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- ROUNDS (real sequence, numbering justified) ---------------- */}
      <section id="how-it-works" className="border-t border-[#3D6E5F]/25">
        <div className="mx-auto max-w-6xl px-6 py-16 md:px-10">
          <div className="grid gap-10 md:grid-cols-3">
            {rounds.map((r) => (
              <div key={r.n}>
                <p className="font-[var(--font-display)] text-3xl text-[#C9A24B]">{r.n}</p>
                <h3 className="mt-3 text-base font-medium">{r.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#F3EFE3]/65">{r.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- CLOSING CTA ---------------- */}
      <section className="border-t border-[#3D6E5F]/25">
        <div className="mx-auto flex max-w-6xl flex-col items-start gap-6 px-6 py-16 md:flex-row md:items-center md:justify-between md:px-10">
          <h2 className="font-[var(--font-display)] text-2xl md:text-3xl">Ready when you are.</h2>
          <Link
            to="/signup"
            className="rounded-full bg-[#C9A24B] px-6 py-3 text-sm font-medium text-[#10241F] transition hover:bg-[#dab566]"
          >
            Create your account
          </Link>
        </div>
      </section>
    </div>
  );
}
