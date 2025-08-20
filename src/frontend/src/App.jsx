import React from 'react';
import Navbar from './components/layout/Navbar';
import Container from './components/ui/Container';
import Button from './components/ui/Button';

function App() {
  const basePath = import.meta?.env?.BASE_URL ?? '/';
  const bg1 = `${basePath}assets/background-1.png`;
  const bg2 = `${basePath}assets/background-2.png`;
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main>
        {/* Section Pertama */}
        <section className="relative overflow-hidden mt-8 min-h-[820px]">
          {/* Background layers */}
          <div className="absolute inset-0 z-0 pointer-events-none select-none">
            <img
              src={bg1}
              alt="bg-1"
              className="absolute inset-x-0 top-0 w-full h-[820px] object-cover"
              style={{
                maskImage: 'linear-gradient(to bottom, black 70%, transparent)',
                WebkitMaskImage: 'linear-gradient(to bottom, black 70%, transparent)'
              }}
            />
            <img
              src={bg2}
              alt="bg-2"
              className="absolute inset-x-0 bottom-0 w-full h-[820px] object-cover opacity-95"
              style={{
                maskImage: 'linear-gradient(to top, black 70%, transparent)',
                WebkitMaskImage: 'linear-gradient(to top, black 70%, transparent)'
              }}
            />
          </div>

          {/* Top blur overlay to blend background with navbar */}
          <div className="absolute inset-x-0 top-0 h-20 sm:h-24 md:h-28 z-[5] pointer-events-none">
            <div className="h-full bg-gradient-to-b from-white/90 via-white/60 to-transparent backdrop-blur-sm md:backdrop-blur-md" />
          </div>

          <Container className="relative z-10 pt-16 pb-24">
            {/* Heading */}
            <div className="text-center">
              <h1 className="text-[34px] sm:text-5xl lg:text-[64px] font-normal tracking-tight text-slate-900">
                Simple, Transparent, Secure
              </h1>
              <p className="mx-auto mt-4 max-w-2xl text-[13px] sm:text-[18px] leading-relaxed text-slate-600">
                Nara Wallet is a chat-first wallet agent for BTC, ETH, and SOL. Create addresses, send or
                receive, buy with card, and see real-time prices with clear, upfront fees.
              </p>
            </div>

            {/* Row 1: Get to know + How it works */}
            <div className="mt-12 flex flex-col md:flex-row items-stretch justify-center gap-6 md:gap-8">
              {/* Card: Get to Know */}
              <div className="relative w-full md:w-[636px] h-auto md:h-[474px] rounded-[28px] border border-slate-200/70 bg-white shadow-[0_15px_60px_rgba(2,6,23,0.06)] ring-1 ring-slate-100 p-8 overflow-hidden">
                <div className="max-w-[520px] pr-28">
                  <h2 className="text-[36px] sm:text-5xl leading-[1.1] font-normal tracking-tight text-slate-900">
                    <span className="block">Get to Know</span>
                    <span className="block">
                      <span className="bg-gradient-to-r from-[#6C8CDF] to-[#2D54B8] bg-clip-text text-transparent font-normal">about</span> Nara Wallet
                    </span>
                  </h2>
                  <p className="mt-5 max-w-xs text-slate-600 text-[15px] leading-relaxed">
                    Agentbot is a chat-first crypto assistant that makes cross-chain transactions simple, safe,
                    and transparent. Manage BTC, ETH, and SOL from one conversation. Our focus are ease of use,
                    fair pricing, and security from day one.
                  </p>
                  <div className="mt-16">
                    <Button size="lg" leftIcon={<img src="/assets/icon-logo.png" className="h-4 w-4" alt="" />}>Get Started</Button>
                  </div>
                </div>
                {/* Phone image */}
                <img
                  src="/assets/Artboard.png"
                  alt="phone"
                  className="pointer-events-none select-none absolute right-[-22px] bottom-[-22px] hidden h-[450px] sm:block"
                />
              </div>

              {/* Card: How it works (dark) */}
              <div className="relative w-full bg-white md:w-[480px] h-auto md:h-[474px] rounded-[28px] border border-white/10 shadow-[0_24px_64px_rgba(2,6,23,0.36)] overflow-hidden p-2">
                <div className="bg-[#070707] text-white rounded-[22px] md:rounded-[24px] w-full h-full pt-8 pr-8 pb-8 overflow-hidden">
                  <h3 className="text-[28px] pl-8 font-normal">How it works</h3>
                  <p className="mt-2 text-[16px] pl-8 font-normal text-white/75 max-w-md leading-relaxed">
                    Chat your request: Agent Wallet handles addresses, balances, transfers, and fiat checkout. Agent Conversion delivers live, compared prices and best picks
                  </p>
                  <img
                    src="/assets/how-it-works2.png"
                    alt="how it works"
                    className="mt-8 w-full max-w-[560px]"
                  />
                </div>
              </div>
            </div>

            {/* Row 2: Nara Wallet + What we do? */}
            <div className="mt-6 flex flex-col md:flex-row items-stretch justify-center gap-6 md:gap-8">
              {/* Card: Feature summary */}
              <div className="rounded-[20px] w-full md:w-[372px] h-auto md:min-h-[596px] border border-slate-200/70 bg-white shadow-[0_15px_60px_rgba(2,6,23,0.06)] ring-1 ring-slate-100 overflow-hidden">
                <div className="px-8 pt-8 pb-6">
                  <div className="flex items-center justify-center">
                    <img src="/assets/logo-nara.png" alt="Nara Wallet logo" className="w-[196px] h-auto" />
                  </div>
                </div>
                <div className="p-2">
                  <img src="/assets/feature.png" alt="feature" className="w-full block" />
                </div>
              </div>

              {/* Card: What we do */}
              <div className="rounded-[20px] w-full md:w-[744px] h-auto md:min-h-[596px] border border-slate-200/70 bg-white shadow-[0_15px_60px_rgba(2,6,23,0.06)] ring-1 ring-slate-100 overflow-hidden">
                <div className="flex items-center justify-between p-8">
                  <div>
                    <h4 className="text-[32px] font-normal text-slate-900">What we do?</h4>
                    <p className="mt-1 text-slate-600 text-[16px]">All crypto actions in single chat! wallet management, send/receive and others.</p>
                  </div>
                  <button className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 text-slate-700 hover:bg-slate-100">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5">
                      <path d="M12.97 5.47a.75.75 0 0 1 1.06 0l5.25 5.25a.75.75 0 0 1 0 1.06l-5.25 5.25a.75.75 0 1 1-1.06-1.06l3.97-3.97H5.75a.75.75 0 0 1 0-1.5h11.19l-3.97-3.97a.75.75 0 0 1 0-1.06Z" />
                    </svg>
                  </button>
                </div>
                <div className="p-2">
                  <img src="/assets/what-we-do.png" alt="what we do" className="w-full block" />
                </div>
              </div>
            </div>
          </Container>
        </section>
      </main>
    </div>
  );
}

export default App;
