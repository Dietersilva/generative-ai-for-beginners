#!/usr/bin/env python3
"""Third batch: the Medicare enrolment cluster, timed for autumn, plus two
under-covered money-saving facts."""

from build_articles import facts, check, AD_INLINE, CHECKED

ARTICLES3 = {}

# ------------------------------------------------------------ enrolment
ARTICLES3['medicare-enrollment'] = {
    'title': 'The Medicare Deadline That Never Forgives You &mdash; The Second Half Guide',
    'eyebrow': 'Facts &amp; thresholds',
    'h1': 'The Medicare deadline that never forgives you',
    'dek': 'Almost every date in this decade is negotiable. This one isn’t &mdash; miss your enrolment '
           'window without the right coverage and you pay a surcharge every month for the rest of your life.',
    'meta': '7 minute read &middot; Verified against Medicare rules and 2026 figures',
    'checked': CHECKED,
    'body': """      <p>We've written a fair amount on this site about how few of the age thresholds in your 60s
      actually matter. Most are marketing. Some are openings rather than deadlines.</p>

      <p>This is the exception, and it's worth being blunt about it. Medicare's late-enrolment penalties
      are permanent. Not a one-off fee, not a penalty that expires after a few years &mdash; a percentage
      added to your monthly premium for as long as you have the coverage. Someone who delays Part B by
      three years without qualifying coverage pays roughly 30% extra <em>every month, for the rest of
      their life</em>.</p>

      <p>The good news is that avoiding it is entirely mechanical. You need to know two things: when your
      window is, and whether your current coverage exempts you.</p>

      <h2>Your Initial Enrolment Period</h2>

      <p>Seven months, centred on the month you turn 65: the three months before, your birthday month,
      and the three months after.</p>

      <p>Enrol in the three months <em>before</em> and coverage generally starts on the first day of your
      birthday month. Enrol during or after, and it starts later &mdash; which can leave a gap. If you
      have a choice, the early part of the window is the better part.</p>

""" + facts('Medicare in 2026', [
        ('$202.90', 'Standard monthly Part B premium. Higher earners pay an income-related surcharge, '
                    'ranging up to $689.90.'),
        ('$283', 'Annual Part B deductible.'),
        ('$38.99', 'The national base premium used to calculate the Part D late penalty.'),
        ('Part B penalty', '10% added for each full 12-month period you could have had Part B and didn’t. '
                           'Permanent.'),
        ('Part D penalty', '1% of $38.99 for every full month you went without creditable drug coverage. '
                           'Permanent, and recalculated annually as the base premium rises.'),
        ('Part A', 'Free for most people &mdash; those with 40 quarters of Medicare-taxed work. That’s '
                   'why Part A rarely carries a penalty.'),
    ]) + """
      <blockquote class="pull">
        <p>Delay Part D by four years and the penalty is roughly 48% of the base premium &mdash; added
        monthly, permanently, to a bill you'll be paying into your nineties.</p>
      </blockquote>

      <h2>The exception that covers most people still working</h2>

      <p>If you're 65 and still employed &mdash; or covered by a spouse's employer plan &mdash; you can
      generally delay Part B without penalty, and pick it up later through a Special Enrolment Period.
      That's eight months from when the employment or the group coverage ends, whichever comes first.</p>

      <p>This is where it goes wrong for people, so read the next paragraph twice.</p>

      <p><strong>COBRA and retiree coverage do not count.</strong> Neither does severance-continued
      coverage. The exemption requires coverage based on <em>current, active employment</em>. Someone who
      retires at 64, takes 18 months of COBRA and assumes they're protected is accumulating penalty
      months the entire time &mdash; and typically discovers it years later, when there is nothing to be
      done about it.</p>

      <p>One further wrinkle if your employer is small: with fewer than 20 employees, Medicare usually
      becomes the <em>primary</em> payer at 65, and the group plan pays second. Delaying Part B in that
      situation can leave you with far less coverage than you think you have. Ask your benefits
      administrator directly whether the plan is primary or secondary once you turn 65. It's a short
      question with a large consequence.</p>

""" + AD_INLINE + """
      <h2>The HSA trap</h2>

      <p>A specific one that catches organised people, because it punishes planning ahead.</p>

      <p>You cannot contribute to a health savings account once you're enrolled in any part of Medicare.
      And when you enrol in Part A after 65, coverage is applied <em>retroactively</em> &mdash; up to six
      months back, though never before your 65th birthday month.</p>

      <p>So contributions made during those retroactive months become excess contributions, with tax
      consequences attached. If you're working past 65 and funding an HSA, stop contributing about six
      months before you plan to enrol. Note also that claiming Social Security automatically enrols you
      in Part A, which means the Social Security decision and the HSA decision are quietly linked.</p>

      <h2>If you’ve already missed it</h2>

      <p>Not ideal, but not hopeless. The General Enrolment Period runs 1 January to 31 March each year,
      and since 2023 coverage begins the month after you sign up rather than waiting until July. The
      penalty still applies, but the gap in coverage is much shorter than it used to be.</p>

      <p>It's also worth knowing that penalties can be waived if you were misled by a government
      representative, and that they don't apply at all if you qualify for Extra Help. Both are worth
      raising rather than assuming.</p>

      <h2>What to actually do</h2>

""" + check([
        'Find your window: count <strong>three months back from your 65th birthday month</strong>, and put '
        'that date in a calendar now. Not a mental note.',
        'Still working? Ask your benefits administrator two questions: <em>is this coverage based on '
        'current employment</em>, and <em>is it primary or secondary once I turn 65?</em>',
        'Never rely on <strong>COBRA or retiree coverage</strong> to protect you from the Part B penalty. '
        'It doesn’t.',
        'Check whether your drug coverage is <strong>creditable</strong> &mdash; your plan must tell you '
        'in writing each year. Keep those letters; they’re your evidence if a penalty is ever assessed '
        'wrongly.',
        'Funding an <strong>HSA</strong> past 65? Stop about six months before you enrol.',
        'Talk to your <strong>SHIP</strong> &mdash; the State Health Insurance Assistance Program. Free, '
        'unbiased, one per state, and they are not selling you a plan. Reach them via <em>shiphelp.org</em> '
        'or 1-800-MEDICARE.',
    ]) + """
      <p>Nearly everything else in this decade can be revisited. Claim Social Security early and you can
      sometimes withdraw or suspend. Choose the wrong Part D plan and you can change it in the autumn.
      Buy the wrong house and you can sell it.</p>

      <p>This one doesn't work that way. Which is why, of all the dates on this site, it's the one worth
      writing down today.</p>
""",
    'sources': [
        ('Medicare &mdash; Avoid late enrolment penalties',
         'https://www.medicare.gov/basics/costs/medicare-costs/avoid-penalties'),
        ('Medicare &mdash; When does Medicare coverage start?',
         'https://www.medicare.gov/basics/get-started-with-medicare/sign-up/when-does-medicare-coverage-start'),
        ('CMS &mdash; 2026 Medicare Parts A &amp; B premiums and deductibles',
         'https://www.cms.gov/newsroom/fact-sheets/2026-medicare-parts-b-premiums-and-deductibles'),
        ('SHIP &mdash; Free local Medicare counselling', 'https://www.shiphelp.org/'),
    ],
    'next': {'slug': 'open-enrollment',
             'title': 'Open enrolment: what the 15 October window is actually for',
             'blurb': 'The annual review most people skip, and the letter in September that tells you '
                      'whether you need it.'},
}

# ------------------------------------------------------------ open enrolment
ARTICLES3['open-enrollment'] = {
    'title': 'Open Enrolment: What the 15 October Window Is Actually For &mdash; The Second Half Guide',
    'eyebrow': 'Facts &amp; thresholds',
    'h1': 'Open enrolment: what the 15 October window is actually for',
    'dek': 'Your plan is allowed to change its costs, its drug list and its doctors every January. '
           'Autumn is the only time most people can respond &mdash; and most don’t.',
    'meta': '6 minute read &middot; Dates and figures current for the 2026&ndash;27 cycle',
    'checked': CHECKED,
    'body': """      <p>Here is the thing that makes Medicare different from almost every other product you buy.</p>

      <p>Your plan can change its premium, its deductible, which drugs it covers, which tier each drug
      sits on, which pharmacies count as preferred, and which doctors are in network &mdash; every single
      January. You don't have to agree. You don't have to be consulted. You'll be told, in a letter, and
      if you do nothing you'll simply be enrolled in the new version.</p>

      <p>Open enrolment is the window in which you're allowed to respond. Most people don't use it. Study
      after study finds that only a minority of enrollees compare plans in any given year, and a
      substantial number could have paid less by switching.</p>

""" + facts('The windows worth knowing', [
        ('15 Oct &ndash; 7 Dec', 'Medicare Open Enrolment. Change Part D plans, switch between Original '
                                 'Medicare and Medicare Advantage, or move between Advantage plans. '
                                 'Changes take effect 1 January.'),
        ('1 Jan &ndash; 31 Mar', 'Medicare Advantage Open Enrolment. If you’re already in an Advantage '
                                 'plan, you get one switch &mdash; to a different Advantage plan or back '
                                 'to Original Medicare.'),
        ('September', 'Your Annual Notice of Change arrives. This is the letter that matters.'),
        ('All year', 'Special Enrolment Periods for qualifying events &mdash; moving, losing other '
                     'coverage, your plan leaving your area, qualifying for Extra Help.'),
    ]) + """
      <h2>The letter not to throw away</h2>

      <p>In September, your plan sends an Annual Notice of Change. It looks like every other piece of
      insurance mail, which is precisely the problem &mdash; it arrives in the same week as the marketing
      and gets treated as more of the same.</p>

      <p>It is not marketing. It's a legally required document listing exactly what's changing about
      <em>your</em> plan in January. Premium, deductible, copays, drug list, network.</p>

      <p>If you read one document this autumn, read that one. Compare it against what you're paying now.
      A great many people discover that the plan they've been happy with for years has quietly moved
      their main medication to a higher tier, or dropped their pharmacy from its preferred network.</p>

      <blockquote class="pull">
        <p>Doing nothing is a decision. It re-enrols you in next year's version of a plan you chose based
        on this year's terms.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>What actually changes year to year</h2>

      <ul>
        <li><strong>Formularies.</strong> Drugs move tiers, get dropped, or acquire new restrictions like
        prior authorisation or step therapy. This is the change most likely to cost you real money.</li>
        <li><strong>Pharmacy networks.</strong> The same drug at the same plan can cost noticeably
        different amounts depending on whether your pharmacy is &ldquo;preferred&rdquo; or merely
        &ldquo;in network.&rdquo;</li>
        <li><strong>Provider networks</strong>, if you're in Medicare Advantage. Doctors and hospitals
        leave networks, sometimes mid-year.</li>
        <li><strong>Premiums and deductibles</strong>, including the Part D deductible, which can be up
        to $615 in 2026.</li>
        <li><strong>Whole plans withdrawing</strong> from a county. If that happens you'll be notified and
        get a Special Enrolment Period &mdash; but you need to act.</li>
      </ul>

      <h2>How to do the review in about twenty minutes</h2>

      <p>The Plan Finder at <em>medicare.gov</em> does the arithmetic, and it's genuinely the best tool in
      government. Enter your actual prescriptions, doses and pharmacy, and it estimates your <strong>total
      annual cost</strong> per plan &mdash; premiums plus deductible plus copays &mdash; rather than the
      premium alone.</p>

      <p>That distinction is the whole exercise. The lowest-premium plan is frequently not the cheapest
      plan for a specific person, and comparing premiums is how people end up paying hundreds more than
      they needed to.</p>

""" + check([
        'Read the <strong>Annual Notice of Change</strong> when it arrives in September. Check your own '
        'medications against the new drug list.',
        'Run the <strong>Plan Finder</strong> with your real prescriptions and your real pharmacy. Compare '
        'estimated <em>annual</em> totals.',
        'In Medicare Advantage? Confirm your <strong>doctors and hospital</strong> are still in network '
        'for next year. Don’t assume.',
        'Check whether your <strong>pharmacy is preferred</strong> under next year’s terms.',
        'Ask your <strong>SHIP counsellor</strong> for help if it’s confusing. Free, unbiased, and they '
        'earn nothing whichever plan you pick &mdash; unlike most people who will call you this autumn.',
        'Get it done before <strong>7 December</strong>. The window doesn’t extend and it doesn’t care why '
        'you missed it.',
    ]) + """
      <p>Twenty minutes, once a year, in a window that's open for seven and a half weeks. It is genuinely
      one of the highest-return uses of time available to anyone on Medicare &mdash; and the main reason
      more people don't do it is that the mail arrives looking exactly like the mail they've learned to
      throw away.</p>
""",
    'sources': [
        ('Medicare &mdash; Joining a plan',
         'https://www.medicare.gov/health-drug-plans/health-plans/your-coverage-options/joining-plan'),
        ('Medicare &mdash; Plan Finder', 'https://www.medicare.gov/plan-compare/'),
        ('Medicare &mdash; Drug coverage costs',
         'https://www.medicare.gov/health-drug-plans/part-d/basics/costs'),
        ('SHIP &mdash; Free local Medicare counselling', 'https://www.shiphelp.org/'),
    ],
    'next': {'slug': 'enrollment-scams',
             'title': 'Why your phone rings more in October',
             'blurb': 'Open enrolment is also the fraud industry’s busiest season. What the rules '
                      'actually permit.'},
}

# ------------------------------------------------------------ enrolment scams
ARTICLES3['enrollment-scams'] = {
    'title': 'Why Your Phone Rings More in October &mdash; The Second Half Guide',
    'eyebrow': 'Protecting yourself',
    'h1': 'Why your phone rings more in October',
    'dek': 'Open enrolment is the one season when unsolicited Medicare contact feels normal. That’s '
           'exactly what makes it the most profitable eight weeks of the fraud calendar.',
    'meta': '5 minute read &middot; Reflects current CMS marketing rules',
    'checked': CHECKED,
    'reader': True,
    'body': """      <p>Between mid-October and early December, the mail gets heavier and the phone starts ringing.
      Some of it is legitimate marketing from real insurers. Some of it is licensed brokers who genuinely
      can help. And some of it is people who want your Medicare number.</p>

      <p>The difficulty is that they all sound roughly the same, and this is the one time of year when a
      call about your Medicare plan feels like it might be expected.</p>

      <p>Which is why the most useful thing to carry into this season isn't a list of scams. It's a clear
      sense of what the rules actually allow &mdash; because a surprising amount of what happens in
      October is already prohibited, and knowing that turns a confusing call into an obvious one.</p>

      <h2>What the rules actually say</h2>

""" + facts('Permitted and not', [
        ('Medicare itself', 'Will not call you out of the blue to sell anything, and will never ask for '
                            'your Medicare number, bank details or a payment over the phone.'),
        ('Unsolicited calls', 'Plans and their agents are generally prohibited from calling you without '
                              'permission. A cold call about your Medicare plan is a red flag on its own.'),
        ('Door-to-door', 'Not allowed without an appointment you arranged.'),
        ('Gifts', 'Agents may not offer cash or gifts above a nominal value to induce enrolment. '
                  '&ldquo;Free&rdquo; gift cards for switching are not a thing.'),
        ('Enrolling you on a call', 'An agent cannot enrol you in a plan during an unsolicited contact.'),
        ('Your Medicare number', 'Treat it like your Social Security number, because it is linked to it. '
                                 'Only your doctors, pharmacists and insurers need it.'),
    ]) + """
      <blockquote class="pull">
        <p>Nearly every legitimate Medicare interaction starts with you. If a conversation began because
        someone contacted you, that alone is worth a pause.</p>
      </blockquote>

      <h2>The scripts that show up this time of year</h2>

      <ul>
        <li><strong>&ldquo;Your plan is being discontinued.&rdquo;</strong> Sometimes plans really do
        leave an area &mdash; and you'd be told in writing by your plan, not by a stranger on the phone.
        Hang up and check the letter.</li>
        <li><strong>&ldquo;You need a new Medicare card.&rdquo;</strong> There is no fee for a
        replacement card and nobody will call to arrange one. This one has been running for years because
        it works.</li>
        <li><strong>Free braces, testing kits or genetic screening.</strong> A durable-medical-equipment
        or lab billing scheme in almost every case. Your number gets used to bill Medicare for equipment
        you didn't need, which can also complicate getting the equipment you later do need.</li>
        <li><strong>&ldquo;I can get you extra benefits.&rdquo;</strong> Often a pitch to move you to a
        plan that pays the caller a commission &mdash; sometimes without making clear you'd be leaving
        Original Medicare and your Medigap policy, which you may not be able to get back on the same
        terms.</li>
        <li><strong>Urgency about the 7 December deadline.</strong> The deadline is real. The pressure to
        decide during the call is not.</li>
      </ul>

""" + AD_INLINE + """
      <h2>The free help almost nobody uses</h2>

      <p>Every state has a <strong>SHIP</strong> &mdash; a State Health Insurance Assistance Program.
      Trained counsellors, free, and structurally unable to profit from your decision. They don't sell
      plans and they earn no commission whichever one you choose.</p>

      <p>That last part is the whole point. A broker may be perfectly honest and still only offer the
      plans they're contracted with. A SHIP counsellor has no such constraint. Find yours at
      <em>shiphelp.org</em> or through 1-800-MEDICARE.</p>

      <p>If you'd rather work with a broker &mdash; and many people reasonably would &mdash; ask two
      questions: which carriers are you appointed with, and how are you paid? An honest broker answers
      both without hesitation.</p>

      <h2>The habit for the season</h2>

""" + check([
        'If <strong>they contacted you</strong>, don’t transact. Hang up and call back on a number you '
        'looked up yourself &mdash; 1-800-MEDICARE, or the number on your plan card.',
        'Never give your <strong>Medicare number</strong> to someone who called, emailed or knocked.',
        'Treat <strong>&ldquo;free&rdquo;</strong> as the warning word. Free equipment, free screening, '
        'free gift for switching &mdash; the item is bait for the number.',
        'Read your <strong>Medicare Summary Notice</strong> or claims at <em>medicare.gov</em> for things '
        'you never received. This is how equipment fraud gets caught.',
        'Report it to <strong>1-800-MEDICARE</strong> and your local <strong>Senior Medicare Patrol</strong> '
        'at <em>smpresource.org</em>. Report even if nothing was lost &mdash; that’s how patterns get found.',
        'Decide nothing on a call you didn’t initiate. You have until <strong>7 December</strong>, and it '
        'is always long enough to check.',
    ]) + """
      <p>The reason this season works so well for fraud isn't that people become careless in October.
      It's that a genuine deadline, real mail from real insurers and a legitimately confusing decision all
      arrive at once &mdash; and confusion plus a deadline is the environment every scam is built for.</p>

      <p>You already have the defence. It's the same one that works the rest of the year: if they
      contacted you, hang up and call back on a number you found yourself.</p>
""",
    'sources': [
        ('Medicare &mdash; Protect yourself from fraud',
         'https://www.medicare.gov/basics/reporting-medicare-fraud-and-abuse'),
        ('CMS &mdash; Medicare marketing rules for plans and agents',
         'https://www.cms.gov/medicare/health-drug-plans/managed-care-marketing'),
        ('Senior Medicare Patrol', 'https://www.smpresource.org/'),
        ('SHIP &mdash; Free local Medicare counselling', 'https://www.shiphelp.org/'),
    ],
    'next': {'slug': 'five-minute-rule',
             'title': 'The five-minute rule',
             'blurb': 'The habit underneath all of this &mdash; and why urgency is the tell that survives '
                      'every change of script.'},
}

# ------------------------------------------------------------ property tax
ARTICLES3['property-tax'] = {
    'title': 'The Property Tax Break You Might Already Qualify For &mdash; The Second Half Guide',
    'eyebrow': 'Facts &amp; thresholds',
    'h1': 'The property tax break you might already qualify for',
    'dek': 'Most states reduce, freeze or defer property taxes once you hit a certain age. Almost none '
           'of them apply it automatically &mdash; and the age is often lower than people assume.',
    'meta': '5 minute read &middot; Programmes vary by state and county &mdash; verify locally',
    'checked': CHECKED,
    'body': """      <p>Property tax is the retirement expense nobody warns you about. It doesn't fall when your
      income does. It doesn't stop when the mortgage is paid off. And in a lot of places it has risen
      considerably faster than Social Security's cost-of-living adjustments.</p>

      <p>What isn't widely known is that nearly every state does something about this for older
      homeowners. Exemptions, assessment freezes, circuit-breaker credits, deferrals. Some are worth a few
      hundred dollars a year and some are worth thousands.</p>

      <p>And here is the part that costs people the most money: <strong>these are almost never
      automatic</strong>. They require an application, they often require renewal, and nobody from the
      county is going to ring you on your 65th birthday to mention it.</p>

      <h2>The four kinds of relief</h2>

""" + facts('What to look for by name', [
        ('Exemption', 'Removes a chunk of your home’s assessed value from taxation. The most common '
                      'form. Sometimes a flat amount, sometimes a percentage.'),
        ('Freeze', 'Locks your assessed value &mdash; or occasionally your actual tax bill &mdash; at the '
                   'level of the year you qualified. Quietly the most valuable type in an area with '
                   'rising values.'),
        ('Circuit breaker', 'A credit or rebate triggered when property tax exceeds a set percentage of '
                            'your income. Usually income-tested, often the most generous for modest incomes.'),
        ('Deferral', 'Lets you postpone payment, usually with interest, until the home is sold or '
                     'transferred. It’s a loan against the house rather than a discount &mdash; useful, '
                     'but understand it as debt.'),
    ]) + """
      <h2>The age is often lower than you’d guess</h2>

      <p>People assume 65. It's frequently earlier: 61 in some states, 62 in several, 60 in a few local
      programmes, and some jurisdictions offer additional relief again at 70 or 75.</p>

      <p>Because thresholds, income limits and application deadlines vary not just by state but sometimes
      by county and school district, this is one of the few topics where we won't print a table of
      specifics &mdash; anything general enough to be safe would be too vague to use, and details this
      granular go stale fast.</p>

      <p>What travels reliably is the method for finding yours.</p>

      <blockquote class="pull">
        <p>The single most expensive assumption here is that the county already knows how old you are and
        will apply it for you.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>How to find out in about half an hour</h2>

""" + check([
        'Search <strong>&ldquo;[your county] assessor senior exemption&rdquo;</strong>. The county '
        'assessor or treasurer administers this, not the state, and their site will list every programme '
        'you might qualify for.',
        'Then search your <strong>state</strong> department of revenue for &ldquo;property tax relief&rdquo; '
        '&mdash; some programmes are state-run and separate from the county’s.',
        'Note the <strong>application deadline</strong>. Many fall early in the year and are strict. '
        'Missing it usually means waiting a full cycle.',
        'Check whether it <strong>renews automatically</strong>. Some need reapplying annually; people '
        'lose benefits they already had this way.',
        'Ask whether relief is <strong>retroactive</strong>. Occasionally you can claim a year or two back. '
        'Usually not &mdash; which is the argument for checking today rather than in the spring.',
        'If income-tested, check <strong>which income</strong> counts. Definitions differ, and some exclude '
        'part or all of Social Security.',
    ]) + """
      <h2>Two things worth knowing before you apply</h2>

      <p><strong>A freeze can be worth far more than an exemption.</strong> A flat exemption saves the
      same amount every year. A freeze compounds &mdash; each year values rise, the gap between your
      frozen assessment and the market widens. In a fast-appreciating area, a freeze claimed at 62 can be
      worth many times an exemption by 75. If you qualify for both, work out which is genuinely better
      over a decade rather than which is bigger today.</p>

      <p><strong>Deferral is a mortgage in disguise.</strong> That's not a reason to dismiss it &mdash;
      for someone house-rich and cash-poor who intends to stay put, it can be exactly the right tool. But
      interest accrues, it becomes a lien, and it reduces what passes to your heirs. Worth a conversation
      with family rather than a quiet decision.</p>

      <p>Also check whether your state offers relief for <strong>veterans</strong>, for people with
      <strong>disabilities</strong>, or for <strong>surviving spouses</strong>. These often stack with
      age-based programmes, and stacking is where the numbers get genuinely large.</p>

      <p>Half an hour on a county website is an unglamorous way to spend a morning. It is also, per
      minute, quite possibly the best-paid work available to a homeowner over 60.</p>
""",
    'sources': [
        ('Lincoln Institute of Land Policy &mdash; Residential property tax relief programmes by state',
         'https://www.lincolninst.edu/publications/other/residential-property-tax-relief-programs/'),
        ('National Council on Aging &mdash; Benefits and assistance for older adults',
         'https://www.ncoa.org/older-adults/benefits/'),
        ('BenefitsCheckUp &mdash; Screening tool for programmes you may qualify for',
         'https://benefitscheckup.org/'),
    ],
    'next': {'slug': 'free-college',
             'title': 'Most states will let you take college classes free after 60',
             'blurb': 'Another benefit that exists nearly everywhere and gets claimed almost nowhere.'},
}

# ------------------------------------------------------------ free college
ARTICLES3['free-college'] = {
    'title': 'Most States Will Let You Take College Classes Free After 60 &mdash; The Second Half Guide',
    'eyebrow': 'Home &amp; everyday life',
    'h1': 'Most states will let you take college classes free after 60',
    'dek': 'Forty-six states have some form of tuition waiver for older residents. Three start at 55. '
           'It is one of the best-kept and least-claimed benefits in the country.',
    'meta': '5 minute read &middot; Programmes vary by state and campus &mdash; verify locally',
    'checked': CHECKED,
    'body': """      <p>This one surprises almost everybody, so let's start with the fact: in all but four states
      &mdash; Arizona, Idaho, Indiana and South Dakota &mdash; there is some statewide provision for
      older residents to take courses at public colleges and universities free or at steeply reduced
      cost.</p>

      <p>Most set the age at 60 or 65. Colorado, Louisiana and Tennessee start at <strong>55</strong>.</p>

      <p>These programmes have existed for decades in many states. They are also dramatically
      under-claimed, mostly because nobody is incentivised to advertise them &mdash; a tuition waiver is,
      by definition, revenue a college isn't collecting.</p>

      <h2>How they generally work</h2>

""" + facts('The shape of most programmes', [
        ('Space available', 'You enrol after fee-paying students have registered. The near-universal '
                            'model &mdash; you fill an empty seat rather than displacing anyone. It also '
                            'means popular courses may be closed to you.'),
        ('Audit or credit', 'Some states cover audit only &mdash; attend and learn, no grade, no credit. '
                            'Others allow full for-credit enrolment, occasionally all the way to a degree.'),
        ('Tuition, not fees', 'The waiver typically covers tuition. Lab fees, technology fees, parking, '
                              'books and materials usually remain yours. Budget a few hundred dollars '
                              'rather than nothing.'),
        ('Residency', 'You’ll generally need to be a resident of the state, sometimes for a minimum period.'),
        ('Public institutions', 'State colleges, universities and community colleges. Private institutions '
                                'set their own rules, and some have their own schemes.'),
    ]) + """
      <p>A few examples of how differently this can look: California residents 60 and over can attend
      California State University campuses tuition-free. Florida residents 60 and over can audit at any
      state university. Ohio residents 60 and over may attend state institutions at no tuition cost. Maine
      requires public universities to offer waivers at 65, for enrichment or toward a degree. Virginia's
      Senior Citizens Higher Education Act covers residents 60 and over, with income conditions attached
      to for-credit study.</p>

      <p>The variation is the point: check your own state rather than assuming your neighbour's rules
      apply.</p>

      <blockquote class="pull">
        <p>Nobody has a commercial reason to tell you this exists. Which is precisely why so few people
        take it up.</p>
      </blockquote>

""" + AD_INLINE + """
      <h2>Audit or credit, and why it matters more than it sounds</h2>

      <p>Auditing is the lower-pressure option: you attend, do as much of the reading as you feel like,
      and nobody grades you. For most people returning to a classroom after forty years, that's the right
      setting &mdash; and it removes the thing that puts people off, which is rarely the material and
      usually the fear of being examined on it.</p>

      <p>For-credit enrolment matters if you want the qualification, or if a structured obligation is what
      actually gets you to turn up. Some people genuinely need the deadline. Know which sort you are
      before choosing.</p>

      <h2>Worth knowing before you go</h2>

""" + check([
        'Search <strong>&ldquo;[your state] senior citizen tuition waiver&rdquo;</strong>, then check the '
        'specific campus &mdash; institutions often apply the state rule with their own conditions.',
        'Call the <strong>registrar’s office</strong>, not admissions. Registrars administer waivers; '
        'admissions staff frequently don’t know the programme exists.',
        'Ask what the <strong>space-available deadline</strong> is. You typically register in the last days '
        'before term, which means having a backup course in mind.',
        'Ask what <strong>fees remain</strong>. This is where the actual cost lives.',
        'Don’t overlook <strong>community colleges</strong>. Often more flexible, more local, more evening '
        'classes, and considerably less intimidating than a large university.',
        'Look up <strong>OLLI</strong> &mdash; Osher Lifelong Learning Institutes, at over 120 universities. '
        'Not free, but designed specifically for older learners, with no exams and no prerequisites.',
    ]) + """
      <p>There's a practical case for this &mdash; the language before the trip, the accounting course,
      the thing you meant to study at 20 and couldn't. There's also a less tidy one that shows up
      repeatedly in research on ageing: sustained mental engagement and regular contact with people
      outside your own generation both matter, and a weekly class delivers both without anyone having to
      call it an intervention.</p>

      <p>Mostly, though, it's a room where somebody who has spent their life on a subject explains it to
      you for free, and you have nothing riding on the exam. That's a good deal at any age. It's a
      remarkable one at 60.</p>
""",
    'sources': [
        ('AARP &mdash; States offering free or low-cost classes for older adults',
         'https://www.aarp.org/work/careers/free-college-classes/'),
        ('BestColleges &mdash; States that offer free tuition for senior citizens',
         'https://www.bestcolleges.com/blog/free-college-tuition-senior-citizens/'),
        ('Osher Lifelong Learning Institutes', 'https://sps.northwestern.edu/oshernrc/'),
    ],
    'next': {'slug': 'property-tax',
             'title': 'The property tax break you might already qualify for',
             'blurb': 'The other benefit hiding in plain sight, and the reason it’s almost never '
                      'applied automatically.'},
}
