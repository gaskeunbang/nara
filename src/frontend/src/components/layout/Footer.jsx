import React from 'react';

export default function Footer() {
    return (
        <footer className="relative w-screen left-1/2 -translate-x-1/2 bg-[#0E0F12] pt-10 text-white">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 py-4">
                <div className="grid grid-cols-1 gap-3 text-center sm:grid-cols-4 sm:gap-6">
                    <div className="sm:text-left">
                        <span className="uppercase tracking-wider text-white/90">(© 2025 NARA WALLET)</span>
                    </div>
                    <a href="#about" className="uppercase tracking-wider text-white/90 hover:text-white">(ABOUT)</a>
                    <a href="#features" className="uppercase tracking-wider text-white/90 hover:text-white">(FEATURES)</a>
                    <a href="#docs" className="uppercase tracking-wider text-white/90 hover:text-white sm:text-right">(DOCUMENTATION)</a>
                </div>
            </div>
        </footer>
    );
}


