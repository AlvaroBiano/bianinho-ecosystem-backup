# @icon-park/react — Verified Icons (v1.9.8, AionUI fork)

Package path: `~/repos/aionui-custom/node_modules/@icon-park/react/es/`

## VERIFIED EXIST ✅

Run this to check any icon:
```bash
ls ~/repos/aionui-custom/node_modules/@icon-park/react/es/icons/ | grep -i "^IconName"
```

### Action / CRUD
| Icon | File | Notes |
|------|------|-------|
| `Plus` | Plus.js | base |
| `PlayOne` | PlayOne.js | ⚠️ NOT `Play` |
| `SaveOne` | SaveOne.js | ⚠️ NOT `Save` |
| `Delete` | Delete.js | |
| `Download` | Download.js | |
| `Refresh` | Refresh.js | |
| `Edit` | Edit.js | ⚠️ NOT `Edit2` |
| `EditOne` | EditOne.js | |
| `Block` | Block.js | use for Trash/Delete |
| `ManualGear` | ManualGear.js | use for Settings/Gear |

### UI Status
| Icon | File | Notes |
|------|------|-------|
| `Check` | Check.js | ⚠️ NOT `CheckCircle` |
| `Error` | Error.js | use for XCircle/fail |
| `Signal` | Signal.js | use for Notification |
| `Timer` | Timer.js | use for Clock |
| `AlarmClock` | AlarmClock.js | |
| `Trend` | Trend.js | use for Chart |
| `Power` | Power.js | |
| `Sync` | Sync.js | |
| `Mute` | Mute.js | ⚠️ NOT `Muted` |
| `Sound` | Sound.js | |

### Files / Docs
| Icon | File | Notes |
|------|------|-------|
| `FileText` | FileText.js | |
| `FileAddition` | FileAddition.js | ⚠️ NOT `FilePlus` |
| `FolderOpen` | FolderOpen.js | |
| `Tag` | Tag.js | |
| `TagOne` | TagOne.js | |
| `Code` | Code.js | |

### Agent / Tech
| Icon | File | Notes |
|------|------|-------|
| `Robot` | Robot.js | |
| `Brain` | Brain.js | |
| `MindMapping` | MindMapping.js | use for Brain if needed |
| `Code` | Code.js | |
| `Terminal` | Terminal.js | |
| `HardDisk` | HardDisk.js | use for Database |
| `Lightning` | Lightning.js | use for Energy |

### Misc
| Icon | File | Notes |
|------|------|-------|
| `Book` | Book.js | |
| `Info` | Info.js | |
| `PreviewOpen` | PreviewOpen.js | ⚠️ NOT `Eye` |
| `TestTube` | TestTube.js | |
| `Flashlamp` | Flashlamp.js | use for Flash/Sparkle |
| `AlarmClock` | AlarmClock.js | |

## CONFIRMED MISSING ❌

These do NOT exist — do not attempt to import them:

```
Clock, Trash, Settings, Gear, Database, CheckCircle, XCircle,
Flash, Energy, Notification, Eye, Edit2, FilePlus, Play, Save,
Shutdown, Muted, Sparkle, CheckCircle, Pluse
```

## Common Substitutions

| Instead of | Use | Reason |
|------------|-----|--------|
| `Play` | `PlayOne` | Play not exported |
| `Save` | `SaveOne` | Save not exported |
| `Eye` | `PreviewOpen` | Eye not exported |
| `Trash` | `Block` | Trash not exported |
| `Settings` | `ManualGear` | Settings not exported |
| `Gear` | `ManualGear` | Gear not exported |
| `CheckCircle` | `Check` | CheckCircle not exported |
| `XCircle` | `Error` | XCircle not exported |
| `Clock` | `Timer` or `AlarmClock` | Clock not exported |
| `Database` | `HardDisk` | Database not exported |
| `Energy` | `Lightning` | Energy not exported |
| `Edit2` | `Edit` | Edit2 not exported |
| `FilePlus` | `FileAddition` | FilePlus not exported |
