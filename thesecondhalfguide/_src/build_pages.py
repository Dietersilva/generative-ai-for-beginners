#!/usr/bin/env python3
"""Build the About / Contact / Privacy pages from a shared stylesheet."""

import sys

HUB = "https://claude.ai/code/artifact/d7289b2f-07da-4008-b5cf-6c2547f70169"

with open('fonts/atkinson-normal-400.b64') as f: A400 = f.read().strip()
with open('fonts/atkinson-normal-700.b64') as f: A700 = f.read().strip()
with open('fonts/atkinson-italic-400.b64') as f: A400I = f.read().strip()
with open('fonts/fraunces-normal-700.b64') as f: F700 = f.read().strip()
with open('fonts/fraunces-italic-500.b64') as f: F500I = f.read().strip()

SHARED_CSS = """
  @font-face { font-family: 'Atkinson Hyperlegible'; font-style: normal; font-weight: 400; font-display: swap; src: url(data:font/woff2;base64,__A400__) format('woff2'); }
  @font-face { font-family: 'Atkinson Hyperlegible'; font-style: normal; font-weight: 700; font-display: swap; src: url(data:font/woff2;base64,__A700__) format('woff2'); }
  @font-face { font-family: 'Atkinson Hyperlegible'; font-style: italic; font-weight: 400; font-display: swap; src: url(data:font/woff2;base64,__A400I__) format('woff2'); }
  @font-face { font-family: 'Fraunces'; font-style: normal; font-weight: 600 700; font-display: swap; src: url(data:font/woff2;base64,__F700__) format('woff2'); }
  @font-face { font-family: 'Fraunces'; font-style: italic; font-weight: 500; font-display: swap; src: url(data:font/woff2;base64,__F500I__) format('woff2'); }

  :root {
    --bg: #FFFDF7;
    --surface: #FFFFFF;
    --surface-2: #FBF3DD;
    --ink: #2E3024;
    --ink-soft: #5C5F4F;
    --ink-faint: #87897A;
    --pine: #3E8267;
    --pine-strong: #2C6650;
    --gold: #E08E2B;
    --gold-soft: #FBE4B8;
    --line: #EDE6D3;
    --focus: #2C6650;
    --shadow: 0 1px 2px rgba(51,53,42,0.05), 0 8px 24px -12px rgba(51,53,42,0.14);
    --radius: 14px;
    color-scheme: light;
  }

  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font-family: 'Atkinson Hyperlegible', 'Segoe UI', system-ui, sans-serif;
    font-size: 19px; line-height: 1.65; -webkit-font-smoothing: antialiased;
  }
  a { color: var(--pine-strong); }
  a:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible {
    outline: 3px solid var(--focus); outline-offset: 3px;
  }

  .wrap { max-width: 740px; margin: 0 auto; padding: 0 28px; }
  .wrap-wide { max-width: 1040px; margin: 0 auto; padding: 0 28px; }

  .topbar {
    position: sticky; top: 0; z-index: 10;
    background: color-mix(in srgb, var(--bg) 88%, transparent);
    backdrop-filter: blur(8px); border-bottom: 1px solid var(--line);
  }
  .topbar .wrap-wide { display: flex; align-items: center; justify-content: space-between; padding: 16px 28px; gap: 16px; }
  .wordmark { font-family: 'Fraunces', serif; font-weight: 700; font-size: 22px; color: var(--ink); text-decoration: none; white-space: nowrap; }
  .wordmark em { font-style: italic; font-weight: 500; color: var(--pine-strong); }
  .topbar-cta { font-size: 16px; font-weight: 700; color: var(--pine-strong); text-decoration: none; white-space: nowrap; border-bottom: 2px solid transparent; }
  .topbar-cta:hover { border-bottom-color: var(--pine-strong); }

  .page-head { padding: 56px 0 8px; }
  .eyebrow {
    display: inline-block; font-size: 13.5px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--pine-strong); background: var(--surface-2); padding: 6px 14px; border-radius: 999px; margin-bottom: 20px;
  }
  h1 {
    font-family: 'Fraunces', serif; font-weight: 700; font-size: clamp(34px, 5vw, 48px);
    line-height: 1.12; letter-spacing: -0.01em; margin: 0 0 18px; text-wrap: balance;
  }
  .dek { font-size: 21px; line-height: 1.6; color: var(--ink-soft); margin: 0 0 22px; max-width: 56ch; }
  .meta { font-size: 15px; color: var(--ink-faint); border-top: 1px solid var(--line); padding-top: 16px; margin-bottom: 8px; }

  .prose { padding: 8px 0 12px; }
  .prose h2 { font-family: 'Fraunces', serif; font-weight: 700; font-size: clamp(23px, 2.9vw, 29px); margin: 44px 0 14px; text-wrap: balance; }
  .prose h3 { font-family: 'Fraunces', serif; font-weight: 700; font-size: 20px; margin: 30px 0 10px; }
  .prose p { margin: 0 0 20px; max-width: 66ch; }
  .prose ul, .prose ol { margin: 0 0 22px; padding-left: 26px; max-width: 64ch; }
  .prose li { margin-bottom: 10px; }
  .prose strong { color: var(--ink); }

  .principles { list-style: none; padding: 0; margin: 0 0 24px; display: flex; flex-direction: column; gap: 14px; }
  .principles li {
    display: flex; gap: 14px; align-items: flex-start; background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: 18px 20px; font-size: 17px;
  }
  .principles svg { flex: none; width: 22px; height: 22px; stroke: var(--pine-strong); margin-top: 2px; }

  .callout {
    display: flex; gap: 14px; margin: 34px 0; padding: 22px 24px; background: var(--surface-2);
    border-radius: var(--radius); border-left: 4px solid var(--gold);
  }
  .callout svg { flex: none; width: 24px; height: 24px; stroke: var(--gold); margin-top: 2px; }
  .callout p { margin: 0; font-size: 16.5px; color: var(--ink-soft); }
  .callout strong { color: var(--ink); }

  .todo {
    margin: 30px 0; padding: 20px 24px; border: 2px dashed var(--gold);
    border-radius: var(--radius); background: color-mix(in srgb, var(--gold-soft) 30%, transparent);
  }
  .todo p { margin: 0; font-size: 16px; color: var(--ink-soft); }
  .todo strong { color: var(--ink); }

  .contact-card {
    display: flex; gap: 18px; align-items: flex-start; margin: 0 0 18px;
    background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius);
    padding: 24px 26px; box-shadow: var(--shadow);
  }
  .contact-card svg { flex: none; width: 26px; height: 26px; stroke: var(--pine-strong); margin-top: 3px; }
  .contact-card h3 { font-family: 'Fraunces', serif; font-weight: 700; font-size: 19px; margin: 0 0 6px; }
  .contact-card p { margin: 0; font-size: 16.5px; color: var(--ink-soft); }
  .contact-card a { font-weight: 700; }

  .toc {
    background: var(--surface-2); border-radius: var(--radius); padding: 22px 26px; margin: 0 0 34px;
  }
  .toc p { font-size: 13.5px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink-faint); margin: 0 0 10px; }
  .toc ol { margin: 0; padding-left: 22px; }
  .toc li { margin-bottom: 6px; font-size: 16.5px; }

  footer { border-top: 1px solid var(--line); padding: 34px 0 60px; margin-top: 48px; }
  .foot-grid { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px 22px; font-size: 15px; color: var(--ink-faint); }
  footer a { color: var(--ink-soft); }
  .foot-links { display: flex; gap: 18px; flex-wrap: wrap; }
"""

SHARED_CSS = (SHARED_CSS
              .replace('__A400I__', A400I)
              .replace('__A400__', A400)
              .replace('__A700__', A700)
              .replace('__F700__', F700)
              .replace('__F500I__', F500I))


def page(title, body, links):
    return f"""<title>{title}</title>
<style>{SHARED_CSS}</style>

<header class="topbar">
  <div class="wrap-wide">
    <a class="wordmark" href="{HUB}">The <em>Second Half</em> Guide</a>
    <a class="topbar-cta" href="{HUB}#ask">Send us a topic &rarr;</a>
  </div>
</header>

<main>
{body}
</main>

<footer>
  <div class="wrap-wide foot-grid">
    <span>&copy; 2026 The Second Half Guide</span>
    <span class="foot-links">
      <a href="{links['about']}">About</a>
      <a href="{links['contact']}">Contact</a>
      <a href="{links['privacy']}">Privacy &amp; Terms</a>
    </span>
  </div>
</footer>
"""


ABOUT_BODY = """  <div class="wrap">
    <div class="page-head">
      <span class="eyebrow">About</span>
      <h1>Why this site exists</h1>
      <p class="dek">Most writing about life after 55 falls into one of two traps: it talks down to you, or it's a sales pitch wearing a cardigan. We're trying to do something plainer than that.</p>
    </div>

    <div class="prose">
      <p>The Second Half Guide is a small, independent site about the practical and the personal side of the years after 55 &mdash; Medicare, Social Security, estate planning, fraud protection, aging in place, travel, family. Some of it is paperwork. Some of it isn't. We think both belong in the same place, because that's how life actually arrives.</p>

      <p>The premise is simple: this stage of life involves a handful of genuinely consequential decisions, most of them explained badly by the people who benefit from your confusion. A Medicare enrollment window is not complicated. It's just described in language designed by a committee. Someone should write it down in normal words.</p>

      <h2>What we promise</h2>
      <ul class="principles">
        <li>
          <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
          <span><strong>Plain language, always.</strong> If a sentence needs a second reading, it's our fault, not yours. We name the jargon once and then stop using it.</span>
        </li>
        <li>
          <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
          <span><strong>We'll show our sources.</strong> Numbers about Social Security, Medicare, or fraud losses come from the agencies that publish them &mdash; SSA, CMS, the FTC, the FBI &mdash; and we say which, so you can check us.</span>
        </li>
        <li>
          <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
          <span><strong>We'll tell you when we don't know.</strong> Where an answer genuinely depends on your situation, we'll say so and point you to the right kind of professional rather than faking precision.</span>
        </li>
        <li>
          <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
          <span><strong>No fear-selling.</strong> Plenty of sites in this space use anxiety to move insurance products. We'd rather you leave a page calmer than you arrived.</span>
        </li>
        <li>
          <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
          <span><strong>Fiction is labeled as fiction.</strong> We publish short stories alongside the practical guides. They're always marked, at the top and the bottom. We won't dress up an invented story as somebody's real life.</span>
        </li>
      </ul>

      <h2>How we're paid</h2>
      <p>This site is free to read and supported by advertising. That arrangement only works if it stays honest, so a few commitments about it:</p>
      <ul>
        <li>Ads are clearly marked as advertisements and kept out of the middle of a sentence you're trying to read.</li>
        <li>Advertisers have no say in what we write. Nobody buys a mention, a recommendation, or a change to an article.</li>
        <li>If we ever earn a commission when you buy something through a link, we'll say so on that page, in plain sight, before the link.</li>
      </ul>

      <h2>How we handle accuracy</h2>
      <p>Rules change &mdash; benefit amounts adjust annually, enrollment ages shift with legislation, scam tactics evolve constantly. Every article carries the reporting year of the figures in it. When the underlying numbers change, we update the article and the date rather than quietly leaving stale advice in place.</p>
      <p>If you find something wrong, tell us. Corrections are one of the more useful things a reader can send, and we'd rather be corrected than trusted for the wrong reasons.</p>

      <div class="callout">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>
        <p><strong>We're a publisher, not an advisor.</strong> Nothing here is personalized financial, legal, medical, or tax advice, and reading it doesn't create a professional relationship. For decisions that turn on your specific numbers, talk to a licensed professional &mdash; ideally bringing our articles as a list of questions to ask.</p>
      </div>

      <h2>Who writes this</h2>
      <p>The Second Half Guide is written and edited by <strong>Edward Silva</strong>.</p>

      <p>I spent more than forty years as a computer professional. That career leaves you with one habit that turns out to be useful here: when somebody hands you a summary, you go and read the actual documentation. Forty years of release notes, specifications and vendor claims will teach anyone to distrust a confident paraphrase.</p>

      <p>I started this site after hitting the age where the mail changes. Medicare postcards, benefit estimates, insurance pitches dressed up as government notices. When I went looking for plain answers, I mostly found two things: writing that talked to me like I'd lost a step, and writing that was really an advertisement. The straightforward facts &mdash; the dates, the thresholds, the dollar figures, the deadline you genuinely cannot miss &mdash; were somehow the hardest part to find.</p>

      <p>So I write them down. I read the primary source, I link to it, and I put the date on it so you know how fresh it is.</p>

      <p>I'm married, with two grown sons, both married themselves &mdash; which is its own education in the family side of this stage of life, and a fair amount of why the site isn't only about paperwork.</p>

      <p>What I am not: a financial adviser, an attorney, an accountant or an insurance agent. I hold no licence and I sell no products. That's a limitation and I'd rather state it plainly than imply otherwise &mdash; this site tells you what the rules say and where to check them. It does not tell you what to do with your money.</p>

      <div class="todo">
        <p><strong>Edward &mdash; two things worth adding here before launch.</strong> First, a photograph of you. Author photos measurably help on exactly this kind of site, and a real face outperforms anything else on this page. Second, read the paragraphs above and change anything that doesn't sound like you &mdash; I've written them from the details you gave me, but the voice should be yours, and it's the one block on the site where that matters most.</p>
      </div>
    </div>
  </div>
"""

CONTACT_BODY = """  <div class="wrap">
    <div class="page-head">
      <span class="eyebrow">Contact</span>
      <h1>Get in touch</h1>
      <p class="dek">Topic requests, corrections, and disagreements all welcome. A real person reads everything that comes in.</p>
    </div>

    <div class="prose">
      <div class="contact-card">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
        <div>
          <h3>General questions and topic ideas</h3>
          <p><a href="mailto:hello@thesecondhalfguide.com">hello@thesecondhalfguide.com</a></p>
        </div>
      </div>

      <div class="contact-card">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4.5"/></svg>
        <div>
          <h3>Corrections</h3>
          <p>Found a number that's out of date or an explanation that's wrong? Send it to <a href="mailto:hello@thesecondhalfguide.com">hello@thesecondhalfguide.com</a> with the article name. We'd genuinely rather know.</p>
        </div>
      </div>

      <div class="contact-card">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h16v12H4z"/><path d="M4 10h16"/></svg>
        <div>
          <h3>Advertising and press</h3>
          <p><a href="mailto:hello@thesecondhalfguide.com">hello@thesecondhalfguide.com</a> &mdash; put &ldquo;advertising&rdquo; in the subject line.</p>
        </div>
      </div>

      <h2>What we can't do</h2>
      <p>We want to be useful, so it's worth being clear about the line we won't cross:</p>
      <ul>
        <li><strong>We can't give you personal advice.</strong> We can't tell you which Medicare plan to choose, when you specifically should claim Social Security, or what to do with your particular retirement account. Those answers depend on details only a licensed professional reviewing your situation should weigh in on.</li>
        <li><strong>Please don't send personal or financial details.</strong> No account numbers, Social Security numbers, medical records, or copies of documents. We don't need them, and email isn't a secure place for them.</li>
        <li><strong>We can't intervene in an active fraud situation.</strong> If money is moving right now, call your bank's fraud line using the number on the back of your card, then report it at <a href="https://reportfraud.ftc.gov">reportfraud.ftc.gov</a> and <a href="https://ic3.gov">ic3.gov</a>. Those calls matter far more than an email to us, and hours count.</li>
      </ul>

      <h2>Response times</h2>
      <p>We're small. Expect a reply within a few business days for most messages. Corrections get looked at first &mdash; if an article is wrong, fixing it beats answering everything else in the queue.</p>

      <div class="callout">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>
        <p><strong>A note on unsolicited email:</strong> we will never email you first asking for money, account access, or personal information. If a message claims to be from us and asks for any of that, it isn't from us &mdash; that's the exact pattern our <em>scam protection</em> coverage exists to warn about.</p>
      </div>
    </div>
  </div>
"""

PRIVACY_BODY = """  <div class="wrap">
    <div class="page-head">
      <span class="eyebrow">Legal</span>
      <h1>Privacy Policy &amp; Terms of Use</h1>
      <p class="dek">What this site collects, what it doesn't, and the terms under which it's offered.</p>
      <p class="meta">Effective August 10, 2026 &middot; Last updated August 10, 2026</p>
    </div>

    <div class="prose">
      <div class="toc">
        <p>On this page</p>
        <ol>
          <li>Information we collect</li>
          <li>Cookies and advertising</li>
          <li>How we use information</li>
          <li>Sharing and disclosure</li>
          <li>Your choices and rights</li>
          <li>Children's privacy</li>
          <li>Data security and retention</li>
          <li>Changes to this policy</li>
          <li>Terms of Use</li>
        </ol>
      </div>

      <h2>1. Information we collect</h2>
      <p>The Second Half Guide (&ldquo;we,&rdquo; &ldquo;us,&rdquo; or &ldquo;this site&rdquo;) is a publication you can read without creating an account. We collect very little directly:</p>
      <ul>
        <li><strong>Information you send us.</strong> If you email us or submit a topic-suggestion form, we receive whatever you choose to include &mdash; typically your message and, if you provide it, your email address. We ask that you not send sensitive personal or financial information.</li>
        <li><strong>Standard technical information.</strong> Like most websites, our hosting infrastructure automatically records ordinary request data such as IP address, browser type, device type, referring page, and the time of your visit.</li>
        <li><strong>Analytics data,</strong> if and when we enable a web analytics service, in the form of aggregate statistics about which pages are read and for how long.</li>
      </ul>
      <p>We do not sell personal information, and we do not run a mailing list unless and until you explicitly sign up for one.</p>

      <h2>2. Cookies and advertising</h2>
      <p>This site is supported by advertising, and advertising involves cookies.</p>
      <ul>
        <li>Third-party vendors, including Google, use cookies to serve ads based on your prior visits to this and other websites.</li>
        <li>Google's use of advertising cookies enables it and its partners to serve ads to you based on your visit to this site and/or other sites on the internet.</li>
        <li>You may opt out of personalized advertising by visiting <a href="https://www.google.com/settings/ads">Google Ads Settings</a>. You can also opt out of third-party vendors' use of cookies for personalized advertising at <a href="https://www.aboutads.info/choices/">aboutads.info/choices</a>.</li>
        <li>Most browsers also let you block or delete cookies through their own settings. Blocking cookies will not prevent you from reading this site.</li>
      </ul>

      <h2>3. How we use information</h2>
      <p>We use the limited information described above to operate and improve the site, to respond to messages you send us, to understand in aggregate which topics readers find useful, to display advertising that funds the site, and to protect against abuse, fraud, and technical problems.</p>

      <h2>4. Sharing and disclosure</h2>
      <p>We do not sell or rent personal information. Information may be handled by service providers acting on our behalf &mdash; web hosting, email delivery, analytics, and advertising partners &mdash; each of which processes data under its own privacy policy. We may also disclose information where required by law or where necessary to protect our legal rights or the safety of others.</p>

      <h2>5. Your choices and rights</h2>
      <p>Depending on where you live, you may have rights regarding your personal information, including the right to request access to it, correction of it, or deletion of it, and the right to opt out of certain processing or of the &ldquo;sale&rdquo; or &ldquo;sharing&rdquo; of personal information as those terms are defined under laws such as the California Consumer Privacy Act. Residents of the European Economic Area and the United Kingdom may have additional rights under the General Data Protection Regulation.</p>
      <p>To make any such request, email <a href="mailto:hello@thesecondhalfguide.com">hello@thesecondhalfguide.com</a>. We will not discriminate against you for exercising these rights.</p>

      <h2>6. Children's privacy</h2>
      <p>This site is intended for adults. We do not knowingly collect personal information from children under 13. If you believe a child has provided us information, contact us and we will delete it.</p>

      <h2>7. Data security and retention</h2>
      <p>We take reasonable measures to protect the limited information we hold, but no method of transmission or storage over the internet is completely secure. We keep correspondence only as long as needed to respond to it and to maintain our records.</p>

      <h2>8. Changes to this policy</h2>
      <p>We may update this policy as the site changes &mdash; for example, if we add a newsletter or an analytics provider. When we do, we will revise the &ldquo;last updated&rdquo; date above. Material changes will be noted on this page.</p>

      <h2>9. Terms of Use</h2>
      <h3>Editorial content is general information only</h3>
      <p>All content on this site is provided for general informational and educational purposes. <strong>It is not financial, legal, medical, tax, or insurance advice,</strong> it is not personalized to your circumstances, and reading it does not create any professional or advisory relationship between you and us. Always consult a qualified, licensed professional before making decisions about your benefits, health coverage, investments, taxes, or estate.</p>

      <h3>Accuracy and currency</h3>
      <p>Benefit amounts, eligibility ages, program rules, and fraud tactics change. We make good-faith efforts to be accurate as of each article's stated reporting period, but we make no warranty that content is current, complete, or error-free. Verify time-sensitive figures with the issuing agency &mdash; such as the Social Security Administration at ssa.gov or Medicare at medicare.gov &mdash; before acting on them.</p>

      <h3>Fiction</h3>
      <p>Some content on this site is clearly labeled as fiction. Characters, towns, and events in those pieces are invented, and any resemblance to real people or events is coincidental.</p>

      <h3>Third-party links and advertising</h3>
      <p>We link to outside sites and display third-party advertising. We do not control and are not responsible for the content, products, accuracy, or privacy practices of any third party, and a link or an advertisement is not an endorsement.</p>

      <h3>Limitation of liability</h3>
      <p>To the fullest extent permitted by law, this site is provided &ldquo;as is,&rdquo; without warranties of any kind, and we are not liable for any loss or damage arising from your use of, or reliance on, its content.</p>

      <h3>Intellectual property</h3>
      <p>Articles, stories, and original graphics on this site are our copyrighted work. You're welcome to quote a short excerpt with a link back; please don't republish full pieces without permission.</p>

      <h3>Governing law and contact</h3>
      <p>These terms are governed by the laws of the State of New York. Questions about this policy or these terms can be sent to <a href="mailto:hello@thesecondhalfguide.com">hello@thesecondhalfguide.com</a>.</p>

      <div class="todo">
        <p><strong>Edward &mdash; two things to settle before launch.</strong> (1) This is a solid, standard policy that reflects how the site actually works today, but it isn't a substitute for review by an attorney licensed in New York &mdash; worth an hour of a lawyer's time before you're monetized, particularly the liability and CCPA/GDPR sections. (2) If you add a newsletter, analytics, or affiliate links later, sections 1, 2, and 4 need updating to match &mdash; a privacy policy that describes practices you don't actually follow is worse than none at all.</p>
      </div>
    </div>
  </div>
"""

PAGES = {
    'about': ('About &mdash; The Second Half Guide', ABOUT_BODY),
    'contact': ('Contact &mdash; The Second Half Guide', CONTACT_BODY),
    'privacy': ('Privacy Policy &amp; Terms &mdash; The Second Half Guide', PRIVACY_BODY),
}


def main():
    # link targets: default to hub until real artifact URLs are known
    links = {'about': HUB, 'contact': HUB, 'privacy': HUB}
    if len(sys.argv) == 4:
        links = {'about': sys.argv[1], 'contact': sys.argv[2], 'privacy': sys.argv[3]}

    for slug, (title, body) in PAGES.items():
        html = page(title, body, links)
        with open(f'{slug}.html', 'w') as f:
            f.write(html)
        print(f'{slug}.html', len(html))


if __name__ == '__main__':
    main()
