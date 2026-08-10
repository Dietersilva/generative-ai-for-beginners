#!/usr/bin/env python3
"""Second batch of articles, rewritten from the draft pack in house style."""

from build_articles import facts, check, AD_INLINE, CHECKED

ARTICLES2 = {}

# ---------------------------------------------------------------- part D cap
ARTICLES2['drug-cap'] = {
    'title': 'The $2,100 Medicare Drug Cap, and What It Doesn’t Cover &mdash; The Second Half Guide',
    'eyebrow': 'Facts &amp; thresholds',
    'h1': 'The $2,100 drug cap: real protection, narrower than it sounds',
    'dek': 'For the first time, Part D prescription costs have a hard annual ceiling. It is a genuinely '
           'big change &mdash; and the phrase &ldquo;out-of-pocket cap&rdquo; is doing a lot of work.',
    'meta': '5 minute read &middot; Verified against Medicare figures for 2026',
    'checked': CHECKED,
    'body': """      <p>If you take expensive medication, $2,100 is the most important number in Medicare this year.</p>

      <p>It's the annual ceiling on what you can pay out of pocket for covered Part D prescription drugs.
      Hit it, and your plan covers your covered drugs for the rest of the calendar year. That is a
      structural change, not a tweak &mdash; for decades, Part D had no upper limit at all, and a
      diagnosis requiring a specialty drug could mean open-ended costs with no ceiling in sight.</p>

      <p>So the cap deserves the attention it's getting. It also gets described inaccurately more often
      than almost any other Medicare number, so it's worth being precise about what it does.</p>

""" + facts('Part D, 2026', [
        ('$2,100', 'Annual out-of-pocket maximum for covered Part D drugs. Includes your deductible, '
                   'copays and coinsurance.'),
        ('$615', 'The highest deductible a Part D plan is allowed to charge. Many plans charge less, and '
                 'some charge nothing.'),
        ('Not included', 'Premiums. What you pay monthly for the plan doesn’t count toward the $2,100.'),
        ('Not included', 'Drugs your plan doesn’t cover, and drugs bought outside the plan &mdash; '
                         'neither counts toward the cap.'),
        ('Not included', 'Everything else in Medicare: hospital stays, doctor visits, tests, Part B drugs, '
                         'dental, vision, hearing.'),
        ('Also available', 'The Medicare Prescription Payment Plan spreads your drug costs across monthly '
                           'instalments. It changes the timing, not the total.'),
    ]) + """
      <h2>What the cap is not</h2>

      <p>&ldquo;Out-of-pocket cap&rdquo; sounds like it means your medical spending stops at $2,100. It
      doesn't. It's a ceiling on <em>one category</em> of cost &mdash; covered prescription drugs bought
      through your Part D plan.</p>

      <p>Two exclusions catch people in particular. Premiums don't count, so a year where you pay the
      full $2,100 plus twelve monthly premiums costs more than $2,100. And drugs your plan doesn't cover
      don't count either &mdash; which is the wrinkle that makes the next section matter more than the
      cap itself.</p>

      <blockquote class="pull">
        <p>The cap protects you brilliantly on the drugs your plan covers. It does nothing at all for the
        drugs it doesn't.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>Why the cap makes plan-shopping more important, not less</h2>

      <p>This is the counter-intuitive part, and it's the reason to keep reading past the headline.</p>

      <p>A cap on covered drugs raises the stakes on the word <em>covered</em>. Plans still maintain their
      own formularies &mdash; the list of drugs they'll pay for. They still sort drugs into tiers with
      different copays. They still run preferred pharmacy networks, and they still apply utilisation
      rules like prior authorisation and step therapy.</p>

      <p>None of that was standardised by the cap. So a plan with an attractive premium can be a poor fit
      for your specific list of medications, and a more expensive plan can produce a lower total for the
      year. The only comparison that means anything is the one run against the drugs you actually take.</p>

      <p>The Medicare Plan Finder at <em>medicare.gov</em> will do this. Enter your prescriptions and your
      pharmacy, and it estimates total annual cost per plan &mdash; premiums plus drug costs, not premiums
      alone. It takes about twenty minutes and it is the single highest-value thing you can do during
      open enrolment.</p>

      <h2>The cash-flow question hiding underneath</h2>

      <p>There's a second, quieter change worth understanding.</p>

      <p>The cap tells you your maximum for the year. It doesn't tell you <em>when</em> you'll pay it. For
      someone on a high-cost drug, costs are often front-loaded &mdash; you can burn through the
      deductible and a large share of the $2,100 in January and February, which is a difficult month or
      two on a fixed income even when the annual total is manageable.</p>

      <p>That's what the Medicare Prescription Payment Plan addresses. It spreads your out-of-pocket drug
      costs into monthly payments across the year instead of charging them at the pharmacy counter. You
      don't pay less &mdash; the total is identical &mdash; but it converts a spike into something
      predictable. For households where the timing was the real problem, that's the useful option, and
      it's easy to miss because it sounds like a discount programme and isn't.</p>

      <h2>Worth doing</h2>

""" + check([
        'Run your <strong>actual prescription list</strong> through the Plan Finder at <em>medicare.gov</em> '
        'during open enrolment. Compare estimated annual totals, not monthly premiums.',
        'Check each drug is <strong>on the formulary</strong> and see which tier it lands on. This matters '
        'more now than it did before the cap.',
        'Check whether your pharmacy is <strong>preferred</strong> in the plan. The same drug at the same '
        'plan can cost different amounts at different counters.',
        'If your costs land heavily in the early months, ask about the <strong>Medicare Prescription '
        'Payment Plan</strong>.',
        'Look into <strong>Extra Help</strong> if money is tight. It’s a separate federal programme '
        'for people with limited income and resources, and it’s widely under-claimed.',
    ]) + """
      <p>The cap is real protection and it removes a genuine fear that hung over people with serious
      conditions. Just don't read it as a ceiling on health costs generally. It's a ceiling on covered
      Part D drugs &mdash; which makes choosing the plan that covers <em>your</em> drugs the decision that
      matters most.</p>
""",
    'sources': [
        ('Medicare &mdash; Drug coverage costs',
         'https://www.medicare.gov/health-drug-plans/part-d/basics/costs'),
        ('Medicare &amp; You 2026 handbook', 'https://www.medicare.gov/publications/10050-medicare-and-you.pdf'),
        ('Medicare &mdash; Prescription Payment Plan',
         'https://www.medicare.gov/prescription-payment-plan'),
    ],
    'next': {'slug': 'senior-age',
             'title': '55, 60, 62, 65: when does &ldquo;senior&rdquo; actually start?',
             'blurb': 'Every age threshold in this decade, including the Medicare window you genuinely '
                      'cannot afford to miss.'},
}

# ---------------------------------------------------------------- POA
ARTICLES2['power-of-attorney'] = {
    'title': 'Power of Attorney: The Document for While You’re Still Here &mdash; The Second Half Guide',
    'eyebrow': 'Paperwork that matters',
    'h1': 'Power of attorney: the document for while you’re still here',
    'dek': 'A will handles what happens after you die. It does nothing for the far more likely problem '
           '&mdash; being alive, and temporarily unable to sign anything.',
    'meta': '6 minute read &middot; General information &mdash; state law varies considerably',
    'checked': CHECKED,
    'body': """      <p>Estate planning conversations orbit death. Understandably &mdash; it's the part everyone knows
      is coming.</p>

      <p>But it leaves a gap, and the gap is statistically more likely to matter first. What happens if
      you're alive and can't handle your own banking? A stroke. A bad fall. Surgery with a longer recovery
      than anyone expected. Cognitive changes that arrive gradually enough that no single day is the day
      it happened.</p>

      <p>The mortgage doesn't pause. Neither does the tax deadline, the insurance premium or the utility
      bill. And here's the part that surprises people: your spouse of forty years generally cannot walk
      into a bank and manage an account with only your name on it. Being married is not legal authority.</p>

      <h2>What the document actually does</h2>

      <p>A financial power of attorney gives someone &mdash; your <em>agent</em>, or attorney-in-fact
      &mdash; legal authority to act on your behalf within the powers the document grants and state law
      permits. Pay bills, manage accounts, deal with insurers, handle property, file taxes.</p>

      <p>The word that matters most is <strong>durable</strong>. A durable power of attorney is written to
      survive your incapacity. A non-durable one ends exactly when you become unable to make decisions
      &mdash; which is to say, at the precise moment you needed it. If you take one thing from this
      article, make it that word.</p>

""" + facts('Four distinctions worth knowing', [
        ('Durable vs. not', 'Durable continues through incapacity. Non-durable ends at it. For planning '
                            'purposes, durable is almost always the point.'),
        ('Immediate vs. springing', 'Immediate takes effect on signing. Springing activates only on a '
                                    'defined event, usually a doctor’s determination &mdash; which sounds '
                                    'safer but can mean delay and argument at the worst moment.'),
        ('Financial vs. medical', 'Two separate documents. A financial POA does not authorise health-care '
                                  'decisions; that’s a health-care proxy or medical power of attorney.'),
        ('Ends at death', 'A POA stops the moment the principal dies. Authority then passes to the '
                          'executor under the will. These are frequently different people.'),
    ]) + """
      <blockquote class="pull">
        <p>A power of attorney is a backup key. The value of a backup key is highest before anybody is
        locked out.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>The risk, stated plainly</h2>

      <p>This document hands someone substantial control over your money with no routine court
      supervision. That is the entire point of it &mdash; and it is also the entire risk.</p>

      <p>The Consumer Financial Protection Bureau is direct about both halves. An agent under a power of
      attorney is a <em>fiduciary</em>: legally required to manage your money for your benefit, not their
      own, to keep your money separate from theirs, and to keep records. Those are real obligations.</p>

      <p>They're also obligations that nobody checks unless something goes wrong and someone complains.
      And financial exploitation of older adults is committed by family members considerably more often
      than by strangers &mdash; a fact that sits awkwardly in an article like this, but leaving it out
      would be worse.</p>

      <p>None of which is an argument against having one. It's an argument for two things: choosing the
      agent carefully, and being deliberate about scope.</p>

      <h2>The powers to think hardest about</h2>

      <p>Some authorities are ordinary. Others deserve a genuine conversation with an attorney, because
      they can permanently redirect where your money ends up:</p>

      <ul>
        <li><strong>The power to make gifts.</strong> Sometimes useful for tax or Medicaid planning.
        Also the single most common route to abuse.</li>
        <li><strong>The power to change beneficiary designations.</strong> Remember that beneficiary
        forms often outrank your will &mdash; so this power can quietly rewrite your estate plan.</li>
        <li><strong>Real estate transactions.</strong> Selling or mortgaging your home.</li>
        <li><strong>Creating or changing trusts.</strong></li>
      </ul>

      <p>A well-drafted document says explicitly whether each of these is granted. A cheap template
      often doesn't, and the ambiguity gets resolved later, expensively, by people who aren't you.</p>

      <h2>Why banks sometimes refuse a valid document</h2>

      <p>A frustration worth anticipating: financial institutions can and do reject powers of attorney.
      The document may be old, or unfamiliar in form, or the bank's legal department may simply want its
      own paperwork. This is maddening but common.</p>

      <p>Two things reduce the odds. Ask each institution now whether they accept a general durable power
      of attorney or require their own form &mdash; many have one, and completing it takes minutes today
      versus weeks of argument later. And refresh the document periodically; a POA signed in 2004 draws
      far more scepticism than one signed recently.</p>

      <h2>Worth doing</h2>

""" + check([
        'Confirm your document says <strong>durable</strong>. If you don’t have one at all, this is '
        'the most commonly skipped document in estate planning and the one most likely to be needed first.',
        'Sort out the <strong>medical side too</strong> &mdash; a health-care proxy and, if you want one, '
        'a living will. The financial POA doesn’t cover any of it.',
        'Ask your bank and brokerage whether they want <strong>their own form</strong>. Do it while it’s '
        'a five-minute errand.',
        'Name a <strong>successor agent</strong> in case your first choice can’t serve. People name a '
        'spouse of similar age and stop there.',
        'Be explicit about <strong>gifts and beneficiary changes</strong> &mdash; granted or withheld, but '
        'not left vague.',
        'Use an attorney licensed in <strong>your state</strong>. This is genuinely state-specific law, and '
        'it’s a modest fee against what a rejected or ambiguous document costs.',
    ]) + """
      <p>People sometimes resist this document because signing it feels like conceding something about
      age. It's closer to the opposite. A power of attorney executed while you are entirely capable is
      you making the choice &mdash; who acts, with what authority, under what limits.</p>

      <p>The alternative isn't that nobody gets that power. It's that a court decides, through
      guardianship proceedings that are slow, public, expensive, and entirely out of your hands.</p>
""",
    'sources': [
        ('CFPB &mdash; What is a power of attorney?',
         'https://www.consumerfinance.gov/ask-cfpb/what-is-a-power-of-attorney-poa-en-1149/'),
        ('CFPB &mdash; Managing someone else’s money',
         'https://www.consumerfinance.gov/consumer-tools/managing-someone-elses-money/'),
        ('CFPB &mdash; Help for agents under a power of attorney',
         'https://files.consumerfinance.gov/f/documents/cfpb_msem_national_agents_guide.pdf'),
    ],
    'next': {'slug': 'beneficiary-form',
             'title': 'Your beneficiary form may outrank your will',
             'blurb': 'The other document that quietly overrides what you thought your estate plan said.'},
}

# ---------------------------------------------------------------- romance
ARTICLES2['romance-scams'] = {
    'title': 'Romance Scams After 55: Intelligence Was Never the Issue &mdash; The Second Half Guide',
    'eyebrow': 'Protecting yourself',
    'h1': 'Romance scams after 55: intelligence was never the issue',
    'dek': 'The strongest ones don’t begin with a request for money. They begin with six months of '
           'someone remembering your grandchildren’s names.',
    'meta': '6 minute read &middot; Reflects current FTC and FBI reporting',
    'checked': CHECKED,
    'reader': True,
    'body': """      <p>Romance fraud is the easiest kind to feel superior about from the outside. That is precisely
      what makes it work.</p>

      <p>The caricature says the victim must have been lonely, naive, or not paying attention. The actual
      mechanism is long-form social engineering, run patiently by people who do this professionally, and
      it is closer to how intelligence services cultivate an asset than to anything you'd recognise as a
      con.</p>

      <p>It is also, year after year, among the highest-loss categories of consumer fraud reported to the
      FTC. Not because a lot of people lose a little. Because some people lose everything.</p>

      <h2>Why it works on capable people</h2>

      <p>A romance scam never asks you to believe one ridiculous thing. It asks you to accept several
      hundred entirely believable things, spread across months.</p>

      <p>Good morning texts. Genuine interest in how the appointment went. Remembering the dog's name,
      and your daughter's new job, and that you don't like being called &ldquo;dear.&rdquo; Photos.
      Setbacks that make the person seem more real, not less. A history accumulates &mdash; and that
      history becomes evidence.</p>

      <p>By the time money enters, the question in your head is not <em>should I send money to a
      stranger?</em> That question would be easy. The question is <em>should I help someone I've known
      for eight months?</em> &mdash; and that question is hard, because for almost everyone, in almost
      every other circumstance, the generous answer is the right one.</p>

      <blockquote class="pull">
        <p>The scam doesn't attack your judgement. It builds a relationship first, then asks your
        judgement to evaluate the relationship.</p>
      </blockquote>

      <h2>Why this stage of life creates specific openings</h2>

      <p>Not gullibility. Circumstance, and arithmetic.</p>

      <p>People in their late 50s and 60s may be dating after a divorce or a death, at an age when the
      old ways of meeting people &mdash; work, mutual friends, the school gate &mdash; have quietly
      closed. Online is where it happens now, for everyone. And this age group has, on average, more
      accumulated assets than a 30-year-old.</p>

      <p>That's the whole story. More reason to be looking, fewer natural channels, and a bigger prize
      for the criminal. The target selection is economic.</p>

""" + AD_INLINE + """
      <h2>The pattern matters more than the person</h2>

      <p>You will not out-research a professional on biography &mdash; the photos are stolen from real
      people, the details are consistent, the backstory is rehearsed. What doesn't vary is the shape:</p>

      <ul>
        <li><strong>They can never meet.</strong> The relationship deepens steadily; the in-person
        meeting is always one obstacle away. This is the closest thing to a single reliable tell.</li>
        <li><strong>Video calls don't happen</strong>, or are brief, dark and troubled by a bad
        connection.</li>
        <li><strong>A crisis arrives at the moment of verification.</strong> Not a coincidence &mdash;
        that's the design. The emergency exists to prevent the check.</li>
        <li><strong>Requests escalate.</strong> A small plausible need first, comfortably repaid. Then a
        larger one. The first is a test.</li>
        <li><strong>An investment opportunity appears.</strong> Increasingly the endgame &mdash; often
        crypto, on a platform that shows healthy gains and permits small withdrawals, right up until it
        doesn't.</li>
        <li><strong>Secrecy and isolation grow.</strong> Family who ask questions are reframed as
        jealous, controlling, or not wanting you to be happy.</li>
      </ul>

      <h2>If it’s someone you love</h2>

      <p>This is the hardest part, and the part most articles skip.</p>

      <p>Opening with &ldquo;how could you fall for this?&rdquo; virtually guarantees the opposite of
      what you want. You've made the choice a referendum on their intelligence and their dignity, which
      means admitting the fraud now costs them humiliation on top of money. Most people will defend the
      relationship harder. Some stop telling their family anything at all, which leaves them alone with
      the only person still talking to them &mdash; the scammer.</p>

      <p>What tends to work better is slower and less satisfying. Stay in the relationship rather than
      issuing ultimatums. Ask questions about the practical shape of things &mdash; when are you two
      finally going to meet? &mdash; rather than pronouncing verdicts. Let doubts be theirs to arrive at.
      A reverse image search on the photos sometimes does more than any argument, because it's evidence
      rather than accusation.</p>

      <p>And separate the person from the fraud. Someone was targeted by a professional criminal. That is
      a thing that happened <em>to</em> them.</p>

      <h2>If it happened to you</h2>

""" + check([
        '<strong>Stop sending money.</strong> Including to recover money already sent &mdash; recovery '
        'scams specifically target people who have already been defrauded, often using stolen victim lists.',
        '<strong>Contact your bank immediately.</strong> Speed matters more than anything else for the '
        'chance of a reversal.',
        '<strong>Report it</strong> at <em>ReportFraud.ftc.gov</em> and <em>ic3.gov</em>. Reporting is also '
        'what generates the data that gets these networks disrupted.',
        '<strong>Keep everything</strong> &mdash; messages, profiles, payment records, account numbers. '
        'Don’t delete in embarrassment; it’s the evidence.',
        '<strong>Tell one person you trust.</strong> Isolation is the mechanism. Breaking it is the '
        'single most protective thing you can do.',
    ]) + """
      <p>Shame is the last tool the scam uses, and the most effective one. It keeps people silent long
      enough for the trail to go cold, and it stops them warning anyone else.</p>

      <p>These are not stories about people who couldn't recognise a fraud. They're stories about
      criminals who understood something true and rather sad about modern life: that genuine attention,
      arriving daily, is scarce enough to be worth a great deal of money to whoever supplies it.</p>
""",
    'sources': [
        ('FTC &mdash; What to know about romance scams',
         'https://consumer.ftc.gov/articles/what-know-about-romance-scams'),
        ('FTC &mdash; Protecting older consumers report',
         'https://www.ftc.gov/reports/protecting-older-consumers-2024-2025-report-congress'),
        ('FBI IC3 &mdash; Confidence fraud and romance scams',
         'https://www.ic3.gov/crimeinfo/romancescams'),
        ('FTC &mdash; Report fraud', 'https://reportfraud.ftc.gov/'),
    ],
    'next': {'slug': 'five-minute-rule',
             'title': 'The five-minute rule',
             'blurb': 'The habit that works against every scam, including the ones nobody has invented yet.'},
}

# ---------------------------------------------------------------- travel ins
ARTICLES2['travel-insurance'] = {
    'title': 'Travel Insurance After 60: What Are You Actually Buying? &mdash; The Second Half Guide',
    'eyebrow': 'Getting out there',
    'h1': 'Travel insurance after 60: what are you actually buying?',
    'dek': 'It gets sold as one checkbox at the end of a booking. It’s at least four different products '
           '&mdash; and the one most people over 65 need isn’t the one they think.',
    'meta': '6 minute read &middot; Medicare coverage rules verified for 2026',
    'checked': CHECKED,
    'body': """      <p>Travel insurance arrives as a single yes-or-no question on the last screen of a booking, priced
      as one number, described in one phrase. That framing is convenient for the seller and unhelpful for
      you, because &ldquo;travel insurance&rdquo; is a bundle of quite different contracts that solve
      quite different problems.</p>

      <p>Buy it without knowing which problem you're solving and you can end up well covered for the risk
      you weren't worried about and uncovered for the one you were.</p>

      <h2>Start here: Medicare mostly stops at the border</h2>

      <p>This is the fact that changes the calculation after 65, and it's the one that surprises people
      most.</p>

      <p><strong>Original Medicare generally does not cover health care outside the United States.</strong>
      There are narrow exceptions &mdash; certain situations involving a ship within six hours of a U.S.
      port, or a foreign hospital closer than the nearest U.S. one &mdash; but they're genuinely narrow.
      For practical purposes, if you're hospitalised in Portugal, Medicare is not paying for it.</p>

      <p>Some Medigap plans do include a foreign travel emergency benefit, and if you have one, you should
      know its shape before you rely on it:</p>

""" + facts('Medigap foreign travel emergency benefit, where included', [
        ('Which plans', 'Generally plans C, D, F, G, M and N. If you have a different letter, check '
                        'before assuming.'),
        ('What it pays', '80% of billed charges for medically necessary emergency care.'),
        ('Deductible', '$250 per year before it pays anything.'),
        ('Time limit', 'Emergency care beginning in the first 60 days of the trip.'),
        ('Lifetime limit', '$50,000 &mdash; not annual. Once used, it’s used.'),
        ('Not covered', 'Routine care, non-emergencies, and generally medical evacuation.'),
    ]) + """
      <p>An $50,000 lifetime cap sounds substantial until you price an air ambulance out of a remote
      region, which can consume most of it by itself. Medicare Advantage plans vary &mdash; some include
      emergency coverage abroad, some don't &mdash; so that's a call to your plan, not an assumption.</p>

      <blockquote class="pull">
        <p>Trip cancellation protects the money you spent on the trip. Travel medical protects you. They
        are not substitutes, and the second one is the one Medicare leaves open.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>The four products wearing one name</h2>

      <p><strong>1. Trip cancellation and interruption.</strong> Reimburses prepaid, non-refundable costs
      when you cancel for a reason <em>listed in the policy</em>. That list is the whole product. Illness,
      injury and a death in the family are typically covered; changing your mind, a work conflict or
      anxiety about a news event typically aren't.</p>

      <p><strong>2. Cancel For Any Reason (CFAR).</strong> An add-on that does roughly what it says, with
      three conditions people miss: it costs meaningfully more, it usually must be bought within a short
      window of your first deposit, and it typically reimburses only 50&ndash;75% of your costs rather
      than all of them.</p>

      <p><strong>3. Travel medical.</strong> Pays for treatment when you get ill or hurt while away. This
      is the gap Medicare leaves. If you're over 65 and going abroad, this is usually the part that
      matters most, and it's frequently the part bundled thinnest.</p>

      <p><strong>4. Medical evacuation and repatriation.</strong> Transport to appropriate care, or home.
      A separate thing again &mdash; a policy that pays a hospital bill does not automatically pay for the
      aircraft that gets you to the hospital. This is the coverage that turns a catastrophic number into a
      manageable one, and it's the reason cruise and expedition travellers buy policies at all.</p>

      <h2>The pre-existing condition clause</h2>

      <p>Most policies exclude claims arising from pre-existing conditions &mdash; usually defined by
      looking back at a window before purchase, often 60 to 180 days, at conditions treated, diagnosed or
      medicated.</p>

      <p>Most insurers also offer a <em>waiver</em> of that exclusion, and it's typically free. The catch
      is timing: you generally have to buy within a short window of your first trip payment, commonly
      14&ndash;21 days, and insure the full trip cost. Miss the window and the waiver is simply
      unavailable, at any price.</p>

      <p>Which produces the single most actionable rule in this article: if you have any ongoing health
      condition and intend to insure a significant trip, buy the policy <strong>right after you make the
      first deposit</strong>, not the week before you fly.</p>

      <h2>When self-insuring is the sensible answer</h2>

      <p>Not every trip needs a policy, and the honest version of this article says so.</p>

      <p>If your bookings are largely refundable, the trip is domestic and inexpensive, and losing the
      cost wouldn't disrupt your finances, a premium to insure a small absorbable loss is poor value. Some
      credit cards also carry trip protection when the trip is paid on that card &mdash; worth checking
      what you already have before buying it twice.</p>

      <p>The real question is never &ldquo;is travel insurance worth it?&rdquo; It's three narrower ones:
      what's already covered, what could I absorb, and what would genuinely hurt?</p>

""" + check([
        'Going abroad and over 65? Check <strong>travel medical and evacuation</strong> first. That’s '
        'the Medicare gap.',
        'Find out whether your <strong>Medigap letter</strong> includes the foreign benefit &mdash; and '
        'remember the $50,000 figure is a lifetime limit.',
        'Any ongoing condition? Buy <strong>within the waiver window</strong> of your first deposit.',
        'Check your <strong>credit card</strong> before buying cancellation cover you may already hold.',
        'Read what counts as a <strong>covered reason</strong>. That list, not the price, is the product.',
        'Match the cover to the trip: a refundable week in Florida and a $25,000 non-refundable expedition '
        'are not the same financial event.',
    ]) + """
      <p>Travel insurance is several contracts sharing a name. Work out which of them you actually need
      and the checkout question stops being a gamble and becomes a purchase.</p>
""",
    'sources': [
        ('Medicare &mdash; Travel outside the U.S.', 'https://www.medicare.gov/coverage/travel-outside-the-u.s.'),
        ('Medicare &mdash; How to compare Medigap policies',
         'https://www.medicare.gov/health-drug-plans/medigap/basics/compare-policies'),
        ('NAIC &mdash; Should I get travel insurance?',
         'https://content.naic.org/article/should-i-get-travel-insurance'),
    ],
    'next': {'slug': 'go-go-years',
             'title': 'The &ldquo;go-go years&rdquo; are real, but they’re not a deadline',
             'blurb': 'Why the countdown-clock version of retirement travel gets the variable wrong.'},
}

# ---------------------------------------------------------------- go-go
ARTICLES2['go-go-years'] = {
    'title': 'The &ldquo;Go-Go Years&rdquo; Are Real, but They’re Not a Deadline &mdash; The Second Half Guide',
    'eyebrow': 'Getting out there',
    'h1': 'The &ldquo;go-go years&rdquo; are real, but they’re not a deadline',
    'dek': 'Retirement planners split later life into go-go, slow-go and no-go. There’s something to it '
           '&mdash; and it has quietly turned a lot of 60s into a countdown clock.',
    'meta': '5 minute read &middot; Health figures from CDC and NIA',
    'checked': CHECKED,
    'body': """      <p>You'll hear the phrase within about ten minutes of any conversation about retirement travel.
      The <em>go-go years</em>, then the slow-go years, then the no-go years.</p>

      <p>It's not nonsense. Mobility and health do change, and pretending otherwise helps nobody. But the
      phrase has escaped its usefulness and become something else &mdash; a countdown, complete with an
      implied expiry date somewhere around 75, and a low hum of urgency underneath every decision about
      whether to take the trip now.</p>

      <p>The data support some caution. They don't support panic, and they certainly don't support a
      deadline.</p>

      <h2>What the numbers actually say</h2>

      <p>Life expectancy at 65 is roughly <strong>19.7 additional years</strong> in the most recent CDC
      figures &mdash; meaning the average 65-year-old has about two more decades, and half will have more
      than that. Meanwhile chronic conditions and mobility limitations do become more common with age, and
      fall risk does rise.</p>

      <p>Both things are true. The mistake is turning a population average into a personal appointment.
      Averages describe a distribution, not your calendar. Plenty of people are hiking hard at 78, and
      some face real limitations at 58 &mdash; and no actuarial table published anywhere knows which one
      you are.</p>

      <blockquote class="pull">
        <p>Averages are not appointments. The clock that matters isn't your age &mdash; it's the
        difficulty of the trip relative to the person taking it.</p>
      </blockquote>

      <h2>The reasonable version of the argument</h2>

      <p>There is a genuine case for doing certain trips sooner, and it deserves stating properly rather
      than being strawmanned.</p>

      <p>Some travel makes unusual physical demands: long walking days on uneven ground, altitude, heat,
      stairs with luggage, expedition boats, remote places far from medical care, itineraries that change
      hotels every second night. If a destination matters deeply to you <em>and</em> requires substantial
      physical capacity, doing it while that capacity is strong is a sound decision, not a fearful one.</p>

      <p>The National Institute on Aging is clear that mobility is closely tied to independence and
      quality of life, and that it responds to what you do. Which cuts both ways: it's a reason to take
      the demanding trip, and equally a reason to keep training so the window stays open longer than the
      brochure assumes.</p>

""" + AD_INLINE + """
      <h2>What the countdown framing gets wrong</h2>

      <p>Three things, and they cost people real money and real experience.</p>

      <p><strong>It rushes expensive decisions.</strong> Urgency is the enemy of good financial judgement
      &mdash; a theme this site keeps running into from different directions. Front-loading heavy
      spending on the assumption that later years won't be worth funding is a bet, and it's a bet made on
      an average rather than on you.</p>

      <p><strong>It assumes travel has one form.</strong> Someone who no longer wants a twelve-mile
      walking day hasn't stopped travelling. They may prefer a month in one apartment in one city, which
      is a deeper experience than three countries in ten days ever was. Rail travel. A cruise. Trips built
      around family, or food, or a language, rather than around exertion.</p>

      <p><strong>It writes off the later decades in advance.</strong> This is the real cost. Treating 75
      as an ending shapes what people plan for, save for, and expect &mdash; and expectations of this
      kind have a way of arranging the outcome.</p>

      <h2>A better question than &ldquo;how old am I?&rdquo;</h2>

      <p>Rank your list by difficulty rather than by urgency. Patagonia, a week in London and a beach
      rental are all &ldquo;travel,&rdquo; and they ask completely different things of a body.</p>

""" + check([
        'Put the <strong>physically demanding trips first</strong> &mdash; not because time is short, but '
        'because difficulty is the variable that actually changes.',
        'Notice that many trips can be made <strong>easier later</strong>: fewer moves, longer stays, '
        'better transport, accessible itineraries. Those aren’t consolation prizes.',
        'Build in <strong>flexibility</strong> &mdash; refundable bookings and travel insurance let you '
        'plan further ahead without betting on your health a year out.',
        'Treat <strong>strength and balance work</strong> as travel equipment. It’s the highest-leverage '
        'thing you can do to keep the window open, and it responds at any age.',
        'Don’t let the countdown push you into spending you can’t comfortably afford. A rushed '
        'trip you paid for with money you needed later is not a good memory.',
    ]) + """
      <p>There's a sensible reason to do the hardest things while they feel easy. There is no scientific
      birthday on which meaningful travel ends, and the people selling you urgency have not met you.</p>

      <p>Sort the list by difficulty. Start at the demanding end. Then keep going for as long as it stays
      good &mdash; which, for a great many people, is considerably longer than the phrase suggests.</p>
""",
    'sources': [
        ('CDC &mdash; FastStats: older persons’ health',
         'https://www.cdc.gov/nchs/fastats/older-american-health.htm'),
        ('National Institute on Aging &mdash; Maintaining mobility and preventing disability',
         'https://www.nia.nih.gov/news/maintaining-mobility-and-preventing-disability-are-key-living-independently-we-age'),
        ('CDC &mdash; Physical activity for older adults',
         'https://www.cdc.gov/physical-activity-basics/guidelines/older-adults.html'),
    ],
    'next': {'slug': 'parks-pass',
             'title': 'The National Parks Senior Pass',
             'blurb': '$80 for life at 62 &mdash; and a genuinely good reason to keep travelling close to home.'},
}

# ---------------------------------------------------------------- grandparent
ARTICLES2['long-distance'] = {
    'title': 'The New Long-Distance Grandparent &mdash; The Second Half Guide',
    'eyebrow': 'Family life',
    'h1': 'The new long-distance grandparent',
    'dek': 'Living far from grandchildren changes the mechanics of closeness. It doesn’t have to change '
           'the closeness &mdash; but it does mean the relationship has to be built rather than absorbed.',
    'meta': '5 minute read &middot; Family life',
    'checked': CHECKED,
    'body': """      <p>Adult children move for work, for housing they can afford, for a relationship, for weather.
      Retirees move too, for most of the same reasons. The result is a family shape that would have been
      unusual two generations ago and is now entirely ordinary: love holding steady while geography
      doesn't.</p>

      <p>Pew found that 55% of U.S. adults live within an hour's drive of at least some extended family
      &mdash; which is another way of saying a very large number don't, and that adults over 65 are not
      exempt from it.</p>

      <p>What follows isn't a consolation prize for people who live far away. Distance genuinely takes
      something away. But it hands back something that nearby grandparents often don't get, and it's
      worth naming.</p>

      <h2>What proximity does better</h2>

      <p>No honest version of this article pretends otherwise. There is no technological substitute for
      ordinary physical presence.</p>

      <p>The nearby grandparent goes to the Tuesday football match. Picks up a sick child at short notice.
      Sits at the kitchen table for an unremarkable hour. That last one is the real advantage &mdash;
      frequency creates familiarity <em>without requiring an event</em>. Nobody has to organise it, and
      nobody is performing.</p>

      <h2>What distance does differently</h2>

      <p>Long-distance relationships are more intentional, and intentional turns out to be surprisingly
      durable.</p>

      <p>A Sunday video call that always happens. A book read aloud a chapter at a time. An online game
      played together on Thursdays. A photo sent whenever something is funny. These become things a child
      <em>expects</em> &mdash; part of the architecture of their week rather than an occasion.</p>

      <p>And there's an advantage nearby grandparents can quietly lose: the long-distance relationship is
      rarely tangled up with childcare logistics. When you're not also the emergency backup, the time you
      do get is undiluted by anyone's stress about the school run.</p>

      <blockquote class="pull">
        <p>Distance removes spontaneity, not intimacy. What it demands is a ritual reliable enough to
        survive a busy week &mdash; on both ends.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>The part nobody controls: their age</h2>

      <p>A three-year-old and a thirteen-year-old experience the same distance completely differently, and
      the approach that worked beautifully has to be replaced roughly every three years.</p>

      <ul>
        <li><strong>Toddlers and young children</strong> need short and frequent rather than long and
        occasional. A ten-minute call twice a week does more than an hour once a month, because at that
        age familiarity decays fast. Doing something on a call &mdash; a book, a puppet, a silly routine
        &mdash; works far better than being asked to converse.</li>
        <li><strong>School-age children</strong> often do best with a shared activity: a game, a project, a
        story continued each week. Something with its own momentum.</li>
        <li><strong>Teenagers</strong> generally will not want a formal family video call, and it isn't
        personal. What often does work is one-to-one and low-pressure &mdash; a text, a link, an interest
        you genuinely share. Being the relative who isn't monitoring their grades is a real position to
        hold.</li>
      </ul>

      <p>Your job changes even when the distance doesn't.</p>

      <h2>The move question</h2>

      <p>Sooner or later this becomes a live conversation, and it deserves both sides.</p>

      <p><strong>For moving closer:</strong> proximity increases the incidental contact that builds
      relationships, makes help easier in both directions, and the window when grandchildren are young is
      genuinely short.</p>

      <p><strong>For staying put:</strong> a move built entirely around adult children can become fragile
      the moment those children relocate again &mdash; and they might, for the same reasons they moved the
      first time. It can also cost you the things that make you a whole person: friends, doctors who know
      your history, a community, a house you like.</p>

      <p>The uncomfortable middle-ground question worth asking honestly: if they moved again in three
      years, would you still be glad you were there? For some people that's an easy yes. For others it's
      the answer.</p>

      <h2>Making it work</h2>

""" + check([
        'Pick a <strong>ritual with a fixed time</strong> and protect it. Reliability beats duration at '
        'every age.',
        'Give the call <strong>something to do</strong> &mdash; a book, a game, a project. Young children '
        'can’t sustain conversation, and shouldn’t have to.',
        'Send things that <strong>arrive physically</strong>. Postcards and small parcels land differently '
        'from anything on a screen, and children keep them.',
        'Agree the <strong>logistics out loud</strong>: who travels, how often, who stays where, who pays. '
        'Families leave this vague and then quietly resent the arrangement they never actually agreed.',
        'Get <strong>one-to-one time</strong> during visits &mdash; an outing with just you and one '
        'grandchild is worth more than three days of general family togetherness.',
        'Build your own life where you live. It makes you better company, and it takes the weight off the '
        'relationship.',
    ]) + """
      <p>Closeness is partly a logistics system, and families tend to focus on the feelings while leaving
      the system unspecified. Who travels, how often, and which small ritual survives a bad week &mdash;
      those quietly determine how much contact actually happens.</p>

      <p>The good news is that a system is buildable. Proximity is largely luck. This part isn't.</p>
""",
    'sources': [
        ('Pew Research Center &mdash; More than half of Americans live within an hour of extended family',
         'https://www.pewresearch.org/short-reads/2022/05/18/more-than-half-of-americans-live-within-an-hour-of-extended-family/'),
        ('Pew Research Center &mdash; The modern American family',
         'https://www.pewresearch.org/social-trends/2023/09/14/the-modern-american-family/'),
    ],
    'next': {'slug': 'on-call',
             'title': 'Being available without being on call',
             'blurb': 'The other grandparenting problem &mdash; the one that comes from living too close.'},
}

# ---------------------------------------------------------------- aging place
ARTICLES2['aging-in-place'] = {
    'title': 'Aging in Place: Staying Home Is a Goal, Not a Plan &mdash; The Second Half Guide',
    'eyebrow': 'Home &amp; everyday life',
    'h1': 'Aging in place: staying home is a goal, not a plan',
    'dek': '&ldquo;I’m never leaving this house&rdquo; sounds like a decision about a house. It’s '
           'mostly a decision about stairs, driving, and who lives near enough to help.',
    'meta': '6 minute read &middot; Home &amp; everyday life',
    'checked': CHECKED,
    'body': """      <p>Almost everyone says it, and they mean it: I want to stay in my own home.</p>

      <p>It's a good goal. It's also, on its own, not a plan &mdash; and the difference shows up years
      later, usually during a week when a decision has to be made quickly and none of the options are
      good.</p>

      <p>Staying home works when the home and the neighbourhood can keep doing their jobs as the person
      living there changes. That's a testable proposition. You can look at a house and a street and form
      a fairly accurate view of how well they'll hold up &mdash; and the earlier you look, the more of
      the answer is still within your control.</p>

      <h2>The thing that decides it usually isn’t the house</h2>

      <p>People imagine the obstacle will be stairs. Often it's the driving.</p>

      <p>A beautiful home can become genuinely isolating if every appointment, every carton of milk and
      every friendship requires getting behind the wheel. Driving is the capability most likely to change
      before mobility does, and it's the one that takes the most with it when it goes &mdash; not just
      logistics, but the casual social contact that keeps people well.</p>

      <p>So the honest first question about aging in place is not <em>can I manage the stairs?</em> It's
      <em>what does a Tuesday look like here if I stop driving?</em> If the answer is &ldquo;nothing
      happens unless someone drives me,&rdquo; that's the finding &mdash; regardless of how good the house
      is.</p>

      <blockquote class="pull">
        <p>The most common mistake is treating this as an architecture problem. It's usually a geography
        problem with an architecture component.</p>
      </blockquote>

      <h2>What actually makes a house workable</h2>

""" + facts('Roughly in order of how much they matter', [
        ('A no-step entry', 'One way into the house without stairs. The single most valuable modification '
                            'and often the least expensive to solve, sometimes with a ramp or regrading.'),
        ('A full bathroom on the main floor', 'Along with a bedroom. Whether single-floor living is '
                                              'possible does more work than any other structural question.'),
        ('Bathroom safety', 'Grab bars fixed into studs &mdash; not suction cups &mdash; a curbless or '
                            'low-threshold shower, a shower seat, a comfort-height toilet.'),
        ('Lighting', 'Dramatically underrated. Vision changes with age, and better light on stairs, '
                     'landings and at entrances prevents more falls than most gadgets.'),
        ('Door widths and handles', 'Thirty-two inches of clear width matters if a walker or wheelchair '
                                    'ever enters the picture. Lever handles beat round knobs for arthritic hands.'),
        ('Flooring', 'Loose rugs are a leading trip hazard and the cheapest fix in this entire table.'),
    ]) + """
""" + AD_INLINE + """
      <h2>Where the money argument goes wrong in both directions</h2>

      <p><strong>Staying is often cheaper &mdash; until it isn't.</strong> A paid-off house looks
      unbeatable next to assisted living costs. But run the whole number: property taxes, insurance,
      maintenance, the roof, the yard work you used to do yourself, the snow removal, and eventually paid
      help in the home. Home care is billed by the hour, and the arithmetic changes sharply once the need
      goes beyond a few hours a week.</p>

      <p><strong>Retrofitting can quietly exceed the value.</strong> Reconfiguring a narrow bathroom or
      working around a split-level can cost more than the difference between your house and one already
      designed for easier living. Occasionally the most economical modification is a different house.</p>

      <p>The framing that helps is not <em>home versus a facility</em>. It's a spectrum: current home,
      modified current home, a smaller accessible home nearby, a home closer to family, independent
      living in a community. Most people never consider the middle options, and the middle is where most
      of the good answers are.</p>

      <h2>The support network is half the plan</h2>

      <p>The National Institute on Aging frames aging in place as depending on both the home and the local
      support around it, and the second half gets much less attention than it deserves.</p>

      <p>Worth knowing before you need it: whether home-care workers are actually available in your area
      and at what rate &mdash; availability varies enormously by region. Who is within a genuine
      short-notice drive. Whether there's an <em>Area Agency on Aging</em> covering your county, because
      there almost certainly is and it's the most under-used resource in this whole subject &mdash;
      transport programmes, meal delivery, home-modification help, benefits screening, often free.</p>

      <h2>Worth doing early</h2>

""" + check([
        'Walk your house and ask: <strong>could I manage here on one floor?</strong> If yes, you’re in '
        'good shape. If no, you now know the project.',
        'Do the <strong>cheap things now</strong> &mdash; lighting, removing loose rugs, properly fixed '
        'grab bars, handrails on both sides of stairs. Small money, disproportionate effect.',
        'When you renovate <strong>anything</strong>, build the future version. A bathroom redone at 62 '
        'should have blocking in the walls for grab bars even if you fit none. It costs almost nothing '
        'during the job and a great deal afterwards.',
        'Answer the <strong>driving question</strong> honestly. It’s the one most likely to decide this.',
        'Look up your <strong>Area Agency on Aging</strong> now, while nothing is wrong. Knowing what '
        'exists locally is most of the value.',
        'Have the <strong>conversation with family</strong> before a crisis picks the answer for you. '
        'Awkward at the kitchen table; far worse from a hospital corridor.',
    ]) + """
      <p>The people who stay in their homes longest are rarely the ones who were most determined about it.
      They're the ones who looked at the house and the street early, fixed the cheap things while it was
      a project rather than an emergency, and stayed honest about what was changing.</p>

      <p>Staying home is the goal. The plan is everything that makes staying possible.</p>
""",
    'sources': [
        ('National Institute on Aging &mdash; Aging in place: growing older at home',
         'https://www.nia.nih.gov/health/aging-place/aging-place-growing-older-home'),
        ('CDC &mdash; Older adult fall prevention',
         'https://www.cdc.gov/falls/about/index.html'),
        ('Eldercare Locator &mdash; Find your Area Agency on Aging',
         'https://eldercare.acl.gov/'),
    ],
    'next': {'slug': 'senior-age',
             'title': '55, 60, 62, 65: when does &ldquo;senior&rdquo; actually start?',
             'blurb': 'The thresholds worth tracking in this decade, and the two with permanent '
                      'consequences.'},
}
