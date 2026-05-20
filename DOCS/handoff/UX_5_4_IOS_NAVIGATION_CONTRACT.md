# UX-5.4 — iOS navigation contract

This doc maps every web route to the SwiftUI navigation primitive it should adopt when Phase D opens. It encodes the locked product decision from the UX-track scope (`memory/project_ux_track_scope.md`):

> **Mobile bottom tabs: Overview / Decision / Replay / Paper + "More" overflow for remaining workspaces.**

The mapping below is the contract: an iOS dev landing in Phase D doesn't need to re-derive it.

## Tab structure

```swift
TabView {
  // The 4 fixed primary tabs — chosen because PMs return to them daily.
  OverviewView()
    .tabItem { Label("Overview", systemImage: "square.grid.2x2") }
    .tag(Tab.overview)

  DecisionWorkspaceView()
    .tabItem { Label("Decision", systemImage: "scope") }
    .tag(Tab.decision)

  ReplayView()
    .tabItem { Label("Replay", systemImage: "clock.arrow.circlepath") }
    .tag(Tab.replay)

  PaperPortfolioView()
    .tabItem { Label("Paper", systemImage: "doc.text") }
    .tag(Tab.paper)

  // "More" is the canonical iOS overflow tab (HIG-blessed pattern for >5 tabs).
  // iOS 18+ auto-renders this as a list when it's the 5th item.
  MoreView()
    .tabItem { Label("More", systemImage: "ellipsis.circle") }
    .tag(Tab.more)
}
.tabViewStyle(.sidebarAdaptable)  // iPad gets a sidebar; iPhone stays bottom tabs
```

## Per-surface mapping

| Web route | Tab | SwiftUI nav primitive | Notes |
|---|---|---|---|
| `/` Overview | Overview | `NavigationStack` | Top-level. Push to Recommendation detail = `NavigationLink(value: rec.id)`. |
| `/decision` Decision Workspace | Decision | `NavigationSplitView` (2-col) | Sidebar = list of recommendations, detail = the workspace. On iPhone the split collapses to a stack automatically. |
| `/comparison` Engine Comparison | More → Comparison | `NavigationStack` | Segmented Picker for view mode (matrix vs alignment chart). |
| `/replay` Replay & Forensics | Replay | Tab root presents a `.fullScreenCover` on launch into the scrubber. | The replay session deserves the whole screen; tab returns to selector when dismissed. |
| `/backtests` Backtests | More → Backtests | `NavigationSplitView` | List of experiments → equity curve detail. |
| `/paper` Paper Portfolio | Paper | `NavigationStack` | Holdings list with `.swipeActions` for accept/defer accelerators (per UX research, never as sole path). |
| `/universe` Universe | More → Universe | `NavigationSplitView` + `.searchable` | Searchable list of universes → constituents detail. |
| `/admin` Ops Command | More → Ops | Web-only redirect on iOS, or a stripped-down "Ops status" tab. | The full pipeline canvas is desktop-only per UX-2.6. |
| `/onboarding` | n/a | `.fullScreenCover` on first launch | Once accepted, persists in `@AppStorage("finrlx-disclaimer-v1")`. |
| `/signup` `/login` | n/a | `.sheet` or root replacement before Tab mounts | Auth gates the entire app. |
| `/disclaimer` `/terms` `/privacy` | More → Legal | `NavigationStack` (push) | Persistent footer link from every recommendation surface (UX-1.4 pattern). |

## Decision Workspace UI mapping (deepest)

The web `/decision` page is the most complex surface. SwiftUI structure:

```swift
NavigationSplitView {
  // Sidebar
  List(recommendations, selection: $selected) { rec in
    Text(rec.ticker).tag(rec.id)
  }
  .listStyle(.sidebar)
} detail: {
  if let rec = recommendations.first(where: { $0.id == selected }) {
    ScrollView {
      VStack(alignment: .leading, spacing: 16) {
        HeroStrip(rec: rec)
        ConfidenceTrio(confidence: rec.confidence)
        ActionStrip(rec: rec)                   // 3 primary CTAs, full-width on iPhone
        EvidenceNarrative(items: rec.evidence)
        EngineDisagreement(agreement: rec.agreement)
        // ... rest of the page surfaces, each its own View
      }
      .padding()
    }
    .toolbar {
      ToolbarItem(placement: .topBarTrailing) {
        Button { /* open context sheet */ } label: { Image(systemName: "info.circle") }
      }
    }
    .sheet(item: $contextSheet) { _ in
      ContextPaneSheet()                        // bottom-sheet equivalent of web's ContextPane
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
    }
  } else {
    ContentUnavailableView("Select a recommendation", systemImage: "scope")
  }
}
```

## ContextPane equivalent

The web `ContextPane` becomes a `.sheet` with detents:

```swift
.sheet(isPresented: $contextOpen) {
  ContextSheetView(tab: $activeTab)
    .presentationDetents([.medium, .large])
    .presentationDragIndicator(.visible)
    .presentationBackgroundInteraction(.enabled(upThrough: .medium))
}
```

`.presentationBackgroundInteraction(.enabled)` is the iOS equivalent of the web's "sheet but main content still scrollable behind the half-height sheet" pattern.

## Disclaimer modal

iOS-native version of the web `DisclaimerModal`:

```swift
.fullScreenCover(isPresented: $needsDisclaimer) {
  DisclaimerView(onAccept: {
    UserDefaults.standard.set("v1", forKey: "finrlx-disclaimer-accepted")
    needsDisclaimer = false
  })
}
```

`.fullScreenCover` (not `.sheet`) because regulatory disclosure must block all other interaction until accepted.

## Accept = no swipe

The locked decision (UX-track scope memory) is **no swipe-to-accept**. SwiftUI implementation:

```swift
// Accept requires an explicit tap into a confirmation sheet.
Button("Publish recommendation") {
  showConfirmSheet = true
}
.confirmationDialog("Publish to paper portfolio?", isPresented: $showConfirmSheet) {
  Button("Publish", role: .destructive) { /* commit */ }
  Button("Cancel", role: .cancel) { }
}

// Defer / Challenge MAY use .swipeActions(allowsFullSwipe: false) as
// accelerators IF they also exist as visible buttons in the row.
.swipeActions(edge: .trailing, allowsFullSwipe: false) {
  Button("Defer") { /* … */ }
  Button("Challenge") { /* … */ }
}
```

## Skip link is unnecessary on iOS

iOS VoiceOver navigates by landmarks natively via the Rotor (single-finger rotate gesture). The web's "Skip to main content" link is a web-specific affordance. No SwiftUI equivalent needed — `accessibilityLabel` on each `View` is enough.

## Final note

When the iOS dev lands in Phase D, this doc plus `UX_5_2_IOS_API_CODEGEN.md`, `frontend/src/design/tokens.json`, and `frontend/src/i18n/en.json` form the complete handoff packet. No more discovery required.
