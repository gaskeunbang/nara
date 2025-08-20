import React, { useState } from 'react';
import Container from '../ui/Container';
import Button from '../ui/Button';

const links = [
    { label: 'Home', href: '#', current: true },
    { label: 'About', href: '#about' },
    { label: 'Features', href: '#features' },
    { label: 'Docs', href: '#docs' },
];

export default function Navbar() {
    const [open, setOpen] = useState(false);

    return (
        <header className="fixed inset-x-0 top-0 z-50  border-slate-200/60 bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/60">
            <Container className="flex h-16 items-center justify-between">
                <a href="#" className="flex items-center gap-3">
                    {/* <img src="/assets/icon-logo.png" alt="Nara" className="h-8 w-8" /> */}
                    <img src="/assets/logo-nara.png" alt="Nara Wallet" className="hidden h-8 md:block" />
                </a>

                <nav className="hidden md:flex items-center gap-10">
                    {links.map((l) => (
                        <a
                            key={l.label}
                            href={l.href}
                            className={`text-sm font-medium transition-colors ${l.current ? 'text-indigo-700' : 'text-slate-600 hover:text-slate-900'
                                }`}
                        >
                            {l.label}
                        </a>
                    ))}
                </nav>

                <div className="hidden md:block">
                    <Button>
                        <span className="inline-flex items-center gap-2">
                            <img src="/assets/icon-logo.png" alt="icon" className="h-4 w-4" />
                            Try it free
                        </span>
                    </Button>
                </div>

                <button
                    aria-label="Toggle menu"
                    className="md:hidden inline-flex h-10 w-10 items-center justify-center rounded-md border border-slate-200 text-slate-700"
                    onClick={() => setOpen((v) => !v)}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-5 w-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                    </svg>
                </button>
            </Container>

            {open ? (
                <div className="md:hidden border-t border-slate-200/60 bg-white">
                    <Container className="py-3">
                        <div className="flex flex-col gap-2">
                            {links.map((l) => (
                                <a key={l.label} href={l.href} className="rounded-md px-2 py-2 text-slate-700 hover:bg-slate-100">
                                    {l.label}
                                </a>
                            ))}
                            <Button className="w-full">Try it free</Button>
                        </div>
                    </Container>
                </div>
            ) : null}
        </header>
    );
}


