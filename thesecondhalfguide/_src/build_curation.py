#!/usr/bin/env python3
"""Build the internal editorial review of the 45-story draft pack."""

from build_pages import SHARED_CSS, HUB, page

EXTRA_CSS = """
  .verdict-table { margin: 26px 0 34px; border: 1px solid var(--line); border-radius: var(--radius); overflow: hidden; background: var(--surface); }
  .verdict-scroll { overflow-x: auto; }
  .verdict-table table { border-collapse: collapse; width: 100%; min-width: 620px; font-size: 16px; }
  .verdict-table th, .verdict-table td { text-align: left; padding: 12px 16px; border-top: 1px solid var(--line); vertical-align: top; }
  .verdict-table thead th { background: var(--surface-2); font-size: 13px; letter-spacing: 0.05em; text-transform: uppercase; color: var(--pine-strong); border-top: none; }
  .verdict-table td.num { color: var(--ink-faint); white-space: nowrap; width: 1%; font-variant-numeric: tabular-nums; }
  .verdict-table td.ttl { font-weight: 700; }

  .tag { display: inline-block; font-size: 12.5px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; padding: 4px 10px; border-radius: 999px; white-space: nowrap; }
  .tag.live { background: #DCEFE4; color: #1F5240; }
  .tag.queue { background: var(--gold-soft); color: #7A4A08; }
  .tag.cut { background: #EFE9E2; color: #6B6257; }

  .stat-row { display: flex; flex-wrap: wrap; gap: 14px; margin: 30px 0 36px; }
  .stat { flex: 1 1 150px; background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); padding: 20px 22px; }
  .stat .n { font-family: 'Fraunces', serif; font-weight: 700; font-size: 34px; line-height: 1; margin-bottom: 6px; }
  .stat .l { font-size: 14.5px; color: var(--ink-soft); }
  .stat.live .n { color: var(--pine-strong); }
  .stat.queue .n { color: #B0741A; }
  .stat.cut .n { color: var(--ink-faint); }

  .rule-box { margin: 30px 0; padding: 24px 28px; background: var(--surface-2); border-radius: var(--radius); border-left: 4px solid var(--pine); }
  .rule-box p { margin: 0 0 12px; }
  .rule-box p:last-child { margin-bottom: 0; }
"""

ROWS_LIVE = [
    ('37', '55, 60, 62, 65: When does &ldquo;senior&rdquo; actually start?',
     'The single best fit for the brief. Pure fact, no advice, and the one piece that defines what the site is.'),
    ('34', 'The Five-Minute Rule',
     'Strong, and the 2025 FBI figures check out. Reframed around the habit rather than the theory.'),
    ('35', 'When the Voice Sounds Like Your Grandchild',
     'Timely and genuinely useful. The &ldquo;verify the event, not the voice&rdquo; distinction is the good idea in the pack.'),
    ('39', 'The National Parks Senior Pass',
     'Lifestyle plus hard numbers. Expanded the &ldquo;what it doesn&rsquo;t cover&rdquo; section, which is where readers get caught.'),
    ('31', 'Your Beneficiary Form May Outrank Your Will',
     'A fact most people genuinely don&rsquo;t know, and checkable in an afternoon. Added the rollover trap.'),
    ('32', 'Who Gets Your Digital Life When You Die?',
     'Modern, distinctive, and almost nobody else in this niche covers it well.'),
    ('05', 'The New $6,000 Senior Deduction',
     'Verified against IRS guidance. Added the correction of the &ldquo;no tax on Social Security&rdquo; headline, which the draft missed.'),
    ('45', 'Being Available Without Being On Call',
     'The warmest piece in the pack and the clearest lifestyle differentiator. Barely needed changing.'),
]

ROWS_LIVE += [
    ('06', 'The $2,100 Medicare Drug Cap', 'Verified. Reframed around what the cap <em>excludes</em> &mdash; premiums, uncovered drugs, all non-drug care.'),
    ('33', 'Power of Attorney', 'Added the durable-vs-springing distinction and why banks reject valid documents.'),
    ('36', 'Romance Scams After 55', 'Kept the draft&rsquo;s respectful tone and added the section on how to talk to someone caught in one.'),
    ('38', 'Travel Insurance After 60', 'Rebuilt around the fact that carries it: Medicare largely stops at the border.'),
    ('41', 'The &ldquo;Go-Go Years&rdquo; Are Not a Deadline', 'Good counterweight to the countdown framing everyone else sells.'),
    ('42', 'The New Long-Distance Grandparent', 'Added what changes as grandchildren age, which the draft skipped.'),
    ('22', 'Aging in Place', 'Trimmed the advice, led with the finding that driving usually decides this before stairs do.'),
]

ROWS_QUEUE = []

ROWS_CUT_ADVICE = [
    ('02', 'Claim Social Security at 62 or 70?'),
    ('04', 'The 60-to-63 Savings Window'),
    ('08', 'The Two-Year Medicare Tax Echo'),
    ('09', 'HSA at 65'),
    ('10', 'The Quiet Years Between Work and RMDs'),
    ('11', 'RMDs at 73'),
    ('12', 'Working While Taking Social Security'),
    ('13', 'The Survivor Check'),
    ('14', 'Annuities: Buying a Pension or Giving Up Control?'),
    ('15', 'Pension Lump Sum or Lifetime Check?'),
    ('16', 'Sequence Risk'),
    ('17', 'The Retirement Spending Smile'),
    ('18', 'Home Equity Is Wealth, But It Isn&rsquo;t Cash'),
    ('19', 'Reverse Mortgages'),
    ('20', 'Downsizing Math'),
    ('21', 'The Retirement Expense Medicare Doesn&rsquo;t Cover'),
    ('23', 'The Family Caregiving Economy'),
    ('43', 'Should Grandparents Help Pay for College?'),
    ('44', 'When Adult Children Still Need Money'),
]

ROWS_CUT_OTHER = [
    ('01', 'Retirement Is Not One Date', 'Thin and abstract. Says less than its own headline.'),
    ('03', 'Medicare Advantage vs. Original Medicare', 'A choice piece, not a fact piece. Replace with a factual Medicare <em>enrollment deadline</em> article &mdash; same traffic, none of the advice exposure.'),
    ('07', 'Retiring Before 65', 'Same problem: structured as a decision, not a fact.'),
    ('24', 'Your Will Is Only Part of the Estate', 'Superseded by #31, which makes the same point far more concretely.'),
    ('25', 'The New Scam Playbook', 'Redundant &mdash; overlaps your existing bank-imposter piece and #34.'),
    ('40', 'Three Long Trips or Ten Short Ones?', 'Redundant with #41, and the weaker of the two.'),
]

ROWS_FICTION = [
    ('26', 'The Tuesday Table'),
    ('27', 'The 61-Year-Old Beginner'),
    ('28', 'He Retired From the Job, Not From Being Useful'),
    ('29', 'The Extra Chair'),
    ('30', 'The Garage With the Light On'),
]


def table(headers, rows):
    head = ''.join(f'<th>{h}</th>' for h in headers)
    body = ''
    for r in rows:
        cells = ''.join(r)
        body += f'              <tr>{cells}</tr>\n'
    return (f'      <div class="verdict-table">\n        <div class="verdict-scroll">\n'
            f'          <table>\n            <thead><tr>{head}</tr></thead>\n'
            f'            <tbody>\n{body}            </tbody>\n'
            f'          </table>\n        </div>\n      </div>\n')


live_rows = [(f'<td class="num">{n}</td>', f'<td class="ttl">{t}</td>',
              f'<td><span class="tag live">Live</span></td>', f'<td>{note}</td>')
             for n, t, note in ROWS_LIVE]

queue_rows = [(f'<td class="num">{n}</td>', f'<td class="ttl">{t}</td>',
               f'<td><span class="tag queue">Queued</span></td>', f'<td>{note}</td>')
              for n, t, note in ROWS_QUEUE]

cut_advice_rows = [(f'<td class="num">{n}</td>', f'<td class="ttl">{t}</td>',
                    f'<td><span class="tag cut">Cut</span></td>')
                   for n, t in ROWS_CUT_ADVICE]

cut_other_rows = [(f'<td class="num">{n}</td>', f'<td class="ttl">{t}</td>', f'<td>{note}</td>')
                  for n, t, note in ROWS_CUT_OTHER]

fiction_rows = [(f'<td class="num">{n}</td>', f'<td class="ttl">{t}</td>') for n, t in ROWS_FICTION]

BODY = """  <div class="wrap">
    <div class="page-head">
      <span class="eyebrow">Editorial review</span>
      <h1>The 45-story pack: what I kept and what I cut</h1>
      <p class="dek">You asked for a 55+ lifestyle page built on facts people need as they near 60 &mdash;
      not an advice page. Measured against that brief, the draft pack splits almost exactly in half.</p>
    </div>

    <div class="prose">
      <div class="stat-row">
        <div class="stat live"><div class="n">15</div><div class="l">Rewritten and published</div></div>
        <div class="stat cut"><div class="n">25</div><div class="l">Cut &mdash; off-brief or redundant</div></div>
        <div class="stat cut"><div class="n">5</div><div class="l">Fiction &mdash; replaced, see below</div></div>
        <div class="stat queue"><div class="n">3</div><div class="l">Fraud pieces now collecting reader stories</div></div>
      </div>

      <h2>The rule I applied</h2>

      <div class="rule-box">
        <p><strong>Keep it if it states a fact with a date, a number or a threshold attached.</strong>
        &ldquo;The Part D cap is $2,100 in 2026.&rdquo; &ldquo;The Senior Pass costs $80 at 62.&rdquo;
        &ldquo;Miss the Medicare window and the penalty is permanent.&rdquo; Those are things a reader
        needs and can act on without anybody advising them.</p>
        <p><strong>Cut it if the core is &ldquo;should you do X with your money?&rdquo;</strong>
        Annuities, sequence risk, pension lump sums, reverse mortgages, whether to help with a
        grandchild&rsquo;s tuition. However well hedged, that is an advice page &mdash; the thing you
        told me you don&rsquo;t want to be.</p>
      </div>

      <p>That line turned out to be unusually clean. It also happens to be the commercially safer side of
      the split: financial-decision content is the hardest category to rank in, gets the most scrutiny
      from Google&rsquo;s quality raters, and carries the most liability for a site with no licensed
      advisor behind it. The pack&rsquo;s own index lists &ldquo;commercial adjacency&rdquo; for every
      piece &mdash; annuities, reverse mortgages, wealth management &mdash; which tells you what it was
      really built for.</p>

      <h2>Published, rewritten in house style</h2>

      <p>All fifteen ran 400&ndash;700 words in the draft and now run 1,050&ndash;1,350. I rewrote the voice
      completely &mdash; the drafts were written in a formal third person with an identical
      &ldquo;the case for / the case against / what changes the answer&rdquo; skeleton on all forty
      pieces, which reads like a template the moment you see two of them side by side.</p>

""" + table(['#', 'Story', 'Status', 'Note'], live_rows) + """
      <h2>Cut: financial advice, not facts</h2>

      <p>Nineteen pieces, all competent, all off-brief. This is the block that would turn the site into
      the thing you said you didn&rsquo;t want. Several are also topics where you&rsquo;d be competing
      directly against Fidelity, Schwab and NerdWallet, who have staff economists and a decade of domain
      authority.</p>

""" + table(['#', 'Story'], cut_advice_rows) + """
      <h2>Cut: thin, redundant, or wrong shape</h2>

""" + table(['#', 'Story', 'Why'], cut_other_rows) + """
      <h2>The five fiction pieces &mdash; my one real objection</h2>

      <p>Stories 26&ndash;30 are invented people. Ellen, Marty, Jean and Luis at the library. The 61-year-old
      beginner. The garage with the light on. They are, for what it&rsquo;s worth, the best-written
      things in the pack &mdash; whoever drafted them can actually write.</p>

      <p>I&rsquo;d still hold them, and I want to be straight about why rather than just filing them
      under &ldquo;cut.&rdquo;</p>

      <ul>
        <li><strong>It undercuts the one thing you&rsquo;re selling.</strong> The site&rsquo;s whole
        proposition is &ldquo;these are the real facts, here&rsquo;s the source, here&rsquo;s the date.&rdquo;
        Publishing invented human stories on the same masthead asks readers to hold two very different
        contracts at once.</li>
        <li><strong>Google&rsquo;s helpful-content guidance leans hard on first-hand experience.</strong>
        Fabricated experience is the exact thing it&rsquo;s designed to catch, and the label may not save it.</li>
        <li><strong>Your audience is being targeted by fakery daily.</strong> You&rsquo;re publishing four
        articles about people impersonating trusted voices. A site for that audience should be unusually
        careful about publishing anything invented, however clearly marked.</li>
      </ul>

      <p><strong>Decided:</strong> the fiction stays unpublished, and the reader-story call is live in
      its place. All three fraud articles now end with &ldquo;Has this happened to you?&rdquo; &mdash;
      an invitation to send what actually happened, published with permission, first names only or fully
      anonymous, and nothing goes up without the reader seeing it first. Each block states plainly that
      the site doesn&rsquo;t invent stories or characters.</p>

      <p>Those five drafts are worth keeping on file as <em>structural</em> templates. When real
      submissions arrive, &ldquo;The Tuesday Table&rdquo; is a good model for how to shape one: a
      specific opening scene, an ordinary middle, no moral hammered at the end.</p>

""" + table(['#', 'Story'], fiction_rows) + """
      <h2>Where the library stands now</h2>

      <p>Nineteen published articles: your original four, plus these fifteen. That is comfortably past
      the point where an AdSense application looks thin, and the topical depth now clusters properly
      &mdash; four fraud pieces, three on paperwork, three on travel, three on family.</p>

      <p>The domain remains the only real blocker. Nothing here can be indexed by Google or approved by
      AdSense while it lives on claude.ai.</p>

      <div class="callout">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>
        <p><strong>One fact-checking note.</strong> The pack was stamped &ldquo;fact-checked through
        August 10, 2026&rdquo; &mdash; which is simply today&rsquo;s date, so I didn&rsquo;t take it at
        face value. I independently verified the load-bearing numbers in everything I published: the
        $2,100 Part D cap, the $6,000 deduction and its $75k/$150k phase-out, the $80 and $20 pass
        prices, and the 2025 FBI elder-fraud figures (201,266 complaints, $7.75 billion). All checked
        out against primary sources. The drafts were more accurate than I expected.</p>
      </div>
    </div>
  </div>
"""

if __name__ == '__main__':
    links = {
        'about': 'https://claude.ai/code/artifact/9547133b-a75a-4f81-b112-6ed4d1034a63',
        'contact': 'https://claude.ai/code/artifact/bde95ba2-582b-4a77-af16-559d0beb862c',
        'privacy': 'https://claude.ai/code/artifact/01d12169-239a-4780-afc1-244fead8ddd6',
    }
    html = page('Editorial review: the 45-story pack &mdash; The Second Half Guide', BODY, links)
    html = html.replace('</style>', EXTRA_CSS + '</style>')
    with open('curation.html', 'w') as f:
        f.write(html)
    print('curation.html', len(html))
