"""
NITK ME318 Centrifugal Pump — v6 (single Impeller body for CFD)
"""
import adsk.core, adsk.fusion, traceback, math, os

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('No active design. Do File > New Design first.')
            return

        rootComp = design.rootComponent

        # ── CLEAR old geometry ──
        while rootComp.features.count > 0:
            try:
                rootComp.features.item(rootComp.features.count - 1).deleteMe()
            except:
                break
        while rootComp.sketches.count > 0:
            try:
                rootComp.sketches.item(rootComp.sketches.count - 1).deleteMe()
            except:
                break
        while rootComp.constructionPlanes.count > 0:
            try:
                rootComp.constructionPlanes.item(
                    rootComp.constructionPlanes.count - 1).deleteMe()
            except:
                break

        sketches = rootComp.sketches
        extrudes = rootComp.features.extrudeFeatures
        conPlanes = rootComp.constructionPlanes
        xyPlane = rootComp.xYConstructionPlane
        zAxis = rootComp.zConstructionAxis

        # ── DIMENSIONS (cm) ──
        IMP_OR   = 2.3    # 23 mm outer radius
        HUB_R    = 0.5    # 5 mm hub radius
        EYE_R    = 0.9    # 9 mm suction eye radius (18mm dia)
        PLATE_T  = 0.2    # 2 mm shroud thickness
        BLADE_H  = 1.2    # 12 mm blade height
        VANE_T   = 0.2    # 2 mm vane thickness
        C        = 0.05   # 0.5 mm axial clearance per side (Option A)

        def pt(x, y, z=0):
            return adsk.core.Point3D.create(x, y, z)
        def val(v):
            return adsk.core.ValueInput.createByReal(v)
        O = pt(0, 0, 0)

        # ════════════════════════════════════════
        #  STEP 1: BACK PLATE (back shroud)
        #  Lifted C = 0.5 mm above housing bottom
        #  so the impeller has clearance on both sides.
        # ════════════════════════════════════════
        backPlaneIn = conPlanes.createInput()
        backPlaneIn.setByOffset(xyPlane, val(C))
        backPlane = conPlanes.add(backPlaneIn)

        sk = sketches.add(backPlane)
        sk.sketchCurves.sketchCircles.addByCenterRadius(O, IMP_OR)
        inp = extrudes.createInput(
            sk.profiles.item(0),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, val(PLATE_T))
        e = extrudes.add(inp)
        e.bodies.item(0).name = 'Back Shroud'

        # ════════════════════════════════════════
        #  STEP 2: HUB (central cylinder)
        # ════════════════════════════════════════
        topPlaneIn = conPlanes.createInput()
        topPlaneIn.setByOffset(backPlane, val(PLATE_T))   # offset from backPlane so vanes sit above back shroud
        topPlane = conPlanes.add(topPlaneIn)

        sk2 = sketches.add(topPlane)
        sk2.sketchCurves.sketchCircles.addByCenterRadius(O, HUB_R)
        inp = extrudes.createInput(
            sk2.profiles.item(0),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, val(BLADE_H))
        e = extrudes.add(inp)
        e.bodies.item(0).name = 'Hub'

        # ════════════════════════════════════════
        #  STEP 3: ONE BACKWARD-CURVED VANE
        #
        #  Uses fitted splines for smooth curves.
        #  Centerline sweeps from 0° at hub to
        #  -60° at rim (dramatic backward curve).
        # ════════════════════════════════════════
        sk3 = sketches.add(topPlane)

        half_t = VANE_T / 2.0   # 0.1 cm

        # Vane centerline at 5 radial stations
        # (radius_cm, angle_degrees)
        centerline = [
            (HUB_R - 0.02,   0.0),
            (0.80,          -12.0),
            (1.20,          -28.0),
            (1.70,          -45.0),
            (IMP_OR,        -60.0),
        ]

        # Compute leading and trailing edge points
        lead_col = adsk.core.ObjectCollection.create()
        trail_col = adsk.core.ObjectCollection.create()

        lead_pts_list = []
        trail_pts_list = []

        for r, a_deg in centerline:
            delta = math.degrees(half_t / r)

            a_lead = math.radians(a_deg + delta)
            lp = pt(r * math.cos(a_lead), r * math.sin(a_lead))
            lead_col.add(lp)
            lead_pts_list.append(lp)

            a_trail = math.radians(a_deg - delta)
            tp = pt(r * math.cos(a_trail), r * math.sin(a_trail))
            trail_col.add(tp)
            trail_pts_list.append(tp)

        # Draw the two edge splines
        spline1 = sk3.sketchCurves.sketchFittedSplines.add(lead_col)
        spline2 = sk3.sketchCurves.sketchFittedSplines.add(trail_col)

        # Close the profile with end-cap lines
        sk3.sketchCurves.sketchLines.addByTwoPoints(
            lead_pts_list[0], trail_pts_list[0])     # hub cap
        sk3.sketchCurves.sketchLines.addByTwoPoints(
            lead_pts_list[-1], trail_pts_list[-1])    # rim cap

        if sk3.profiles.count < 1:
            ui.messageBox(
                'Vane profile failed!\n'
                'Curves: {}, Profiles: {}'.format(
                    sk3.sketchCurves.count, sk3.profiles.count))
            return

        # Pick smallest profile (the vane, not any outer region)
        vIdx = 0
        if sk3.profiles.count > 1:
            minA = 1e10
            for i in range(sk3.profiles.count):
                a = sk3.profiles.item(i).areaProperties().area
                if a < minA:
                    minA = a
                    vIdx = i

        inp = extrudes.createInput(
            sk3.profiles.item(vIdx),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, val(BLADE_H))
        vaneExt = extrudes.add(inp)
        vaneExt.bodies.item(0).name = 'Vane 1'

        # ════════════════════════════════════════
        #  STEP 4: CIRCULAR PATTERN (6 vanes)
        # ════════════════════════════════════════
        col = adsk.core.ObjectCollection.create()
        col.add(vaneExt)
        cpIn = rootComp.features.circularPatternFeatures.createInput(
            col, zAxis)
        cpIn.quantity = val(6)
        cpIn.totalAngle = val(2 * math.pi)
        cpIn.isSymmetric = False
        rootComp.features.circularPatternFeatures.add(cpIn)

        # ════════════════════════════════════════
        #  STEP 5: FRONT SHROUD (with eye hole)
        #  Annular disc on top of the vanes
        # ════════════════════════════════════════
        frontPlaneIn = conPlanes.createInput()
        frontPlaneIn.setByOffset(backPlane, val(PLATE_T + BLADE_H))  # backPlane + shroud + blades
        frontPlane = conPlanes.add(frontPlaneIn)

        sk5 = sketches.add(frontPlane)
        sk5.sketchCurves.sketchCircles.addByCenterRadius(O, IMP_OR)
        sk5.sketchCurves.sketchCircles.addByCenterRadius(O, EYE_R)

        # Find the annular profile (2 loops = ring between circles)
        annularProf = None
        for pi in range(sk5.profiles.count):
            p = sk5.profiles.item(pi)
            if p.profileLoops.count == 2:
                annularProf = p
                break
        if annularProf is None and sk5.profiles.count > 0:
            # Fallback: pick the larger area profile
            maxA = 0
            for pi in range(sk5.profiles.count):
                p = sk5.profiles.item(pi)
                a = p.areaProperties().area
                if a > maxA and p.profileLoops.count > 1:
                    maxA = a
                    annularProf = p
            if annularProf is None:
                annularProf = sk5.profiles.item(0)

        inp = extrudes.createInput(
            annularProf,
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        inp.setDistanceExtent(False, val(PLATE_T))
        e = extrudes.add(inp)
        e.bodies.item(0).name = 'Front Shroud'

        # ════════════════════════════════════════
        #  STEP 5b: MERGE ALL IMPELLER PARTS → ONE BODY
        #
        #  For CFD with Moving Reference Frame (MRF), the
        #  entire rotating assembly must be a SINGLE body.
        #  At this point ONLY impeller bodies exist:
        #    Back Shroud + Hub + Vane 1 + 5 pattern copies
        #    + Front Shroud  =  9 separate bodies.
        #  We join them all into Back Shroud (the base body)
        #  and rename the result 'Impeller'.
        # ════════════════════════════════════════
        impBaseBody = None
        impToolCol  = adsk.core.ObjectCollection.create()
        for bi in range(rootComp.bRepBodies.count):
            b = rootComp.bRepBodies.item(bi)
            if b.name == 'Back Shroud':
                impBaseBody = b
            else:
                impToolCol.add(b)

        if impBaseBody is not None and impToolCol.count > 0:
            impJoinInp = rootComp.features.combineFeatures.createInput(
                impBaseBody, impToolCol)
            impJoinInp.operation = \
                adsk.fusion.FeatureOperations.JoinFeatureOperation
            impJoinInp.isKeepToolBodies = False
            rootComp.features.combineFeatures.add(impJoinInp)
            # Rename the merged body
            for bi in range(rootComp.bRepBodies.count):
                if rootComp.bRepBodies.item(bi).name == 'Back Shroud':
                    rootComp.bRepBodies.item(bi).name = 'Impeller'
                    break
        else:
            ui.messageBox(
                'Step 5b FAILED: Could not merge impeller parts!\n'
                'Bodies found: ' + ', '.join([
                    rootComp.bRepBodies.item(i).name
                    for i in range(rootComp.bRepBodies.count)]))

        # ════════════════════════════════════════
        #  STEP 6: VOLUTE CASING
        #  Spiral path is drawn at the AXIAL MID-SPAN of the
        #  blade zone so the tube is centred inside the housing.
        #    VOLUTE_Z = PLATE_T + BLADE_H/2 = 0.2 + 0.6 = 0.8 cm
        #  Cross-section planes are perpendicular to the spiral,
        #  so tube circles are centred at this Z height.
        # ════════════════════════════════════════
        VOLUTE_Z = C + PLATE_T + BLADE_H / 2.0  # 0.85 cm (C + shroud + blade midspan)
        volutePlaneIn = conPlanes.createInput()
        volutePlaneIn.setByOffset(xyPlane, val(VOLUTE_Z))
        volutePlane = conPlanes.add(volutePlaneIn)
        skP = sketches.add(volutePlane)
        spts = adsk.core.ObjectCollection.create()
        for d in range(0, 271, 15):
            th = math.radians(d)
            r = 2.90 + 0.30 * d / 270.0
            spts.add(pt(r * math.cos(th), r * math.sin(th)))
        spts.add(pt(0, -5.20))
        spline = skP.sketchCurves.sketchFittedSplines.add(spts)

        fracs       = [0.01, 0.29, 0.58, 0.88, 0.99]
        radii       = [0.150, 0.200, 0.275, 0.350, 0.500]  # bore (inner) radii
        VOLUTE_WALL = 0.15   # 1.5 mm tube wall thickness
        outer_radii = [r + VOLUTE_WALL for r in radii]

        # ── 6a: OUTER SOLID LOFT ──────────────────────────────
        #  One circle per plane → profiles.item(0) = full solid disc.
        #  No ring-profile ambiguity; Fusion always gets this right.
        outerProfs = []
        for i in range(5):
            pIn = conPlanes.createInput()
            pIn.setByDistanceOnPath(spline, val(fracs[i]))
            pl = conPlanes.add(pIn)
            sO = sketches.add(pl)
            sO.sketchCurves.sketchCircles.addByCenterRadius(
                pt(0, 0, 0), outer_radii[i])
            if sO.profiles.count > 0:
                outerProfs.append(sO.profiles.item(0))

        if len(outerProfs) == 5:
            lf = rootComp.features.loftFeatures
            li = lf.createInput(
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            for p in outerProfs:
                li.loftSections.add(p)
            try:
                cp = adsk.fusion.Path.create(
                    spline,
                    adsk.fusion.ChainedCurveOptions.noChainedCurves)
                li.centerLineOrRails.addCenterLine(cp)
            except:
                pass
            lr = lf.add(li)
            try:
                lr.bodies.item(0).name = 'Volute Outer'
            except:
                pass

        # ── 6b: INNER SOLID LOFT ──────────────────────────────
        #  Same path, smaller circles → the bore volume to subtract.
        innerProfs = []
        for i in range(5):
            pIn = conPlanes.createInput()
            pIn.setByDistanceOnPath(spline, val(fracs[i]))
            pl = conPlanes.add(pIn)
            sI = sketches.add(pl)
            sI.sketchCurves.sketchCircles.addByCenterRadius(
                pt(0, 0, 0), radii[i])
            if sI.profiles.count > 0:
                innerProfs.append(sI.profiles.item(0))

        if len(innerProfs) == 5:
            lf = rootComp.features.loftFeatures
            li = lf.createInput(
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            for p in innerProfs:
                li.loftSections.add(p)
            try:
                cp = adsk.fusion.Path.create(
                    spline,
                    adsk.fusion.ChainedCurveOptions.noChainedCurves)
                li.centerLineOrRails.addCenterLine(cp)
            except:
                pass
            lr = lf.add(li)
            try:
                lr.bodies.item(0).name = 'Volute Inner'
            except:
                pass

        # ── 6c: SUBTRACT INNER FROM OUTER → hollow tube ───────
        #  CutFeatureOperation: Outer - Inner = thin-walled tube.
        #  'Volute Inner' body is consumed; result kept as 'Volute Casing'.
        voluteOuter = None
        voluteInner = None
        for bi in range(rootComp.bRepBodies.count):
            nm = rootComp.bRepBodies.item(bi).name
            if nm == 'Volute Outer': voluteOuter = rootComp.bRepBodies.item(bi)
            if nm == 'Volute Inner': voluteInner = rootComp.bRepBodies.item(bi)

        if voluteOuter is not None and voluteInner is not None:
            toolCol = adsk.core.ObjectCollection.create()
            toolCol.add(voluteInner)
            cutInp6 = rootComp.features.combineFeatures.createInput(
                voluteOuter, toolCol)
            cutInp6.operation = \
                adsk.fusion.FeatureOperations.CutFeatureOperation
            cutInp6.isKeepToolBodies = True   # keep 'Volute Inner' for Step 11c spiral cut
            rootComp.features.combineFeatures.add(cutInp6)
            for bi in range(rootComp.bRepBodies.count):
                if rootComp.bRepBodies.item(bi).name == 'Volute Outer':
                    rootComp.bRepBodies.item(bi).name = 'Volute Casing'
                    break
        else:
            ui.messageBox(
                'Step 6c FAILED: could not find Volute Outer / Inner.\n'
                'Bodies: ' + ', '.join([
                    rootComp.bRepBodies.item(i).name
                    for i in range(rootComp.bRepBodies.count)]))

        # ════════════════════════════════════════
        #  STEP 7: (MERGED INTO STEP 11b)
        #  Cutting the volute inner face here then joining
        #  with a solid housing disc causes the housing
        #  material to back-fill the opening.
        #  Instead, ONE bore cut AFTER the join (Step 11b)
        #  simultaneously opens the impeller chamber AND
        #  the spiral inlet — correct order, cleaner result.
        # ════════════════════════════════════════
        CUTWATER_R = 2.90   # 29 mm — exact cutwater radius
        CUT_H      = 4.40   # 44 mm total → ±22 mm each side
                             # clears housing top (HSG_H = 17 mm) with 5 mm margin
                             # NOTE: setSymmetricExtent() takes TOTAL distance → each side = CUT_H/2

        # ════════════════════════════════════════
        #  STEP 8: HOUSING DRUM
        #  Compact SOLID cylinder — impeller drum.
        #  R = 3.10 cm (31 mm)
        #    = CUTWATER_R (29 mm) + 2 mm outer wall
        #  H = 1.70 cm (17 mm)  [Option A clearance fix]
        #    = impeller stack (16 mm) + 2 × C (2 × 0.5 mm)
        #    Impeller sits C = 0.5 mm above housing bottom
        #    and C = 0.5 mm below housing top — no contact.
        #
        #  The spiral tube (centred at R=2.9→3.2 cm)
        #  wraps clearly around the OUTSIDE of this drum.
        #  Step 11b bores the impeller chamber (R<2.9 cm)
        #  through the joined Casing body.
        # ════════════════════════════════════════
        HSG_R = 3.10          # 31 mm — compact drum outer wall
        HSG_H = 1.60 + 2 * C  # 17 mm — impeller stack (16 mm) + 0.5 mm clearance each side

        skHsg = sketches.add(xyPlane)
        skHsg.sketchCurves.sketchCircles.addByCenterRadius(O, HSG_R)

        hsgInp = extrudes.createInput(
            skHsg.profiles.item(0),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        hsgInp.setDistanceExtent(False, val(HSG_H))
        hsgFeat = extrudes.add(hsgInp)
        hsgFeat.bodies.item(0).name = 'Housing'

        # ════════════════════════════════════════
        #  STEP 10: SHAFT HOLE THROUGH IMPELLER
        #  R = 0.5 cm (5 mm) — motor shaft slides
        #  up through the back shroud section.
        #  Symmetric cut centred at xyPlane (Z=0):
        #    each side = C + PLATE_T + 0.10 cm = 0.35 cm
        #    → cuts Z = -0.35 → +0.35 cm
        #    → clears Back Shroud (Z=C→C+PLATE_T) ✓
        #  participantBodies = [Impeller] ensures the
        #  hole only appears in the rotating assembly.
        # ════════════════════════════════════════
        SHAFT_R = 0.50   # 5 mm — matches hub radius

        # Find the merged Impeller body
        impellerBody = None
        for bi in range(rootComp.bRepBodies.count):
            if rootComp.bRepBodies.item(bi).name == 'Impeller':
                impellerBody = rootComp.bRepBodies.item(bi)
                break

        if impellerBody is not None:
            skShaft = sketches.add(xyPlane)
            skShaft.sketchCurves.sketchCircles.addByCenterRadius(O, SHAFT_R)
            shaftInp = extrudes.createInput(
                skShaft.profiles.item(0),
                adsk.fusion.FeatureOperations.CutFeatureOperation)
            # Symmetric cut: total = 2*(C + PLATE_T + margin)
            # Covers the Back Shroud region of the Impeller (Z = C → C+PLATE_T)
            shaftInp.setSymmetricExtent(val(2.0 * (C + PLATE_T + 0.10)), True)
            shaftInp.participantBodies = [impellerBody]
            extrudes.add(shaftInp)
        else:
            ui.messageBox('Step 10 FAILED: Impeller body not found!')

        # ════════════════════════════════════════
        #  STEP 11: JOIN VOLUTE INTO HOUSING
        #  Boolean union: Housing + Volute Casing
        #  = one single 'Casing' body.
        #  Volute body is consumed. Body count: 11 → 10.
        #  Impeller bodies are NOT touched.
        # ════════════════════════════════════════
        housingBody3 = None
        voluteBody2  = None
        for bi in range(rootComp.bRepBodies.count):
            nm = rootComp.bRepBodies.item(bi).name
            if nm == 'Housing':
                housingBody3 = rootComp.bRepBodies.item(bi)
            if nm == 'Volute Casing':
                voluteBody2 = rootComp.bRepBodies.item(bi)

        if housingBody3 is not None and voluteBody2 is not None:
            toolCol2 = adsk.core.ObjectCollection.create()
            toolCol2.add(voluteBody2)

            joinInp = rootComp.features.combineFeatures.createInput(
                housingBody3, toolCol2)
            joinInp.operation = \
                adsk.fusion.FeatureOperations.JoinFeatureOperation
            joinInp.isKeepToolBodies = False
            rootComp.features.combineFeatures.add(joinInp)

            # Rename the merged body to 'Casing'
            for bi in range(rootComp.bRepBodies.count):
                if rootComp.bRepBodies.item(bi).name == 'Housing':
                    rootComp.bRepBodies.item(bi).name = 'Casing'
                    break
        else:
            ui.messageBox(
                'Step 11 FAILED:\n'
                'Housing found: {}\n'
                'Volute found: {}'.format(
                    housingBody3 is not None,
                    voluteBody2  is not None))

        # ════════════════════════════════════════
        #  STEP 11b: IMPELLER BORE CUT THROUGH CASING
        #  Cut a cylinder R = CUTWATER_R (29 mm) through
        #  the joined Casing body in one go.
        #  This single cut does TWO things:
        #    1. Carves the impeller chamber (central bore)
        #    2. Opens the inner face of each volute
        #       cross-section so impeller discharge can
        #       enter the spiral channel — correct fluid
        #       path from impeller to outlet.
        #  participantBodies restricts cut to Casing only;
        #  all impeller bodies are untouched.
        # ════════════════════════════════════════
        casingBody = None
        for bi in range(rootComp.bRepBodies.count):
            if rootComp.bRepBodies.item(bi).name == 'Casing':
                casingBody = rootComp.bRepBodies.item(bi)
                break

        if casingBody is not None:
            skBore = sketches.add(xyPlane)
            skBore.sketchCurves.sketchCircles.addByCenterRadius(O, CUTWATER_R)
            boreInp = extrudes.createInput(
                skBore.profiles.item(0),
                adsk.fusion.FeatureOperations.CutFeatureOperation)
            boreInp.setSymmetricExtent(val(CUT_H), True)
            boreInp.participantBodies = [casingBody]
            extrudes.add(boreInp)
        else:
            ui.messageBox('Step 11b FAILED: Casing body not found for bore cut!')

        # ════════════════════════════════════════
        #  STEP 11c: CUT SPIRAL CHANNEL THROUGH CASING
        #  Problem: the boolean JOIN (Step 11) fills the hollow
        #  bore of the volute tube with housing solid material.
        #  Fix: use the preserved 'Volute Inner' body (the exact
        #  bore volume) to cut that material back out of Casing.
        #  After this cut the spiral fluid channel is fully open
        #  from the impeller chamber into the volute at every
        #  point along the spiral — correct flow path.
        #  'Volute Inner' is consumed (isKeepToolBodies = False).
        # ════════════════════════════════════════
        casingBody2  = None
        voluteInner2 = None
        for bi in range(rootComp.bRepBodies.count):
            nm = rootComp.bRepBodies.item(bi).name
            if nm == 'Casing':       casingBody2  = rootComp.bRepBodies.item(bi)
            if nm == 'Volute Inner': voluteInner2 = rootComp.bRepBodies.item(bi)

        if casingBody2 is not None and voluteInner2 is not None:
            toolCol3 = adsk.core.ObjectCollection.create()
            toolCol3.add(voluteInner2)
            spiralCutInp = rootComp.features.combineFeatures.createInput(
                casingBody2, toolCol3)
            spiralCutInp.operation = \
                adsk.fusion.FeatureOperations.CutFeatureOperation
            spiralCutInp.isKeepToolBodies = False   # consume Volute Inner
            rootComp.features.combineFeatures.add(spiralCutInp)
        else:
            ui.messageBox(
                'Step 11c FAILED:\n'
                'Casing found:       {}\n'
                'Volute Inner found: {}'.format(
                    casingBody2  is not None,
                    voluteInner2 is not None))

        # ════════════════════════════════════════
        #  STEP 12: FRONT COVER PLATE
        #  Solid disc on TOP of housing.
        #  R = 3.8 cm (same as housing outer R)
        #  T = 0.2 cm (2 mm thick)
        #  Placed at Z = HSG_H (top of housing).
        #  Next step cuts the eye hole through it.
        # ════════════════════════════════════════
        COVER_T = 0.20   # 2 mm thick

        # Plane at top face of housing (Z = HSG_H)
        coverPlaneIn = conPlanes.createInput()
        coverPlaneIn.setByOffset(xyPlane, val(HSG_H))
        coverPlane = conPlanes.add(coverPlaneIn)

        skCover = sketches.add(coverPlane)
        skCover.sketchCurves.sketchCircles.addByCenterRadius(
            pt(0, 0, 0), HSG_R)

        covInp = extrudes.createInput(
            skCover.profiles.item(0),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        covInp.setDistanceExtent(False, val(COVER_T))
        covFeat = extrudes.add(covInp)
        covFeat.bodies.item(0).name = 'FrontCover'

        # ════════════════════════════════════════
        #  STEP 13: EYE HOLE THROUGH FRONT COVER
        #  Cut R = 0.9 cm (9 mm) = ∅18 mm
        #  This is the inlet eye — fluid enters here.
        #  Targets FrontCover body ONLY.
        #  Casing and impeller are NOT touched.
        # ════════════════════════════════════════

        # Find FrontCover body
        coverBody = None
        for bi in range(rootComp.bRepBodies.count):
            if rootComp.bRepBodies.item(bi).name == 'FrontCover':
                coverBody = rootComp.bRepBodies.item(bi)
                break

        if coverBody is not None:
            # Sketch on the front cover plane (Z = HSG_H)
            skEye = sketches.add(coverPlane)
            skEye.sketchCurves.sketchCircles.addByCenterRadius(
                pt(0, 0, 0), EYE_R)   # EYE_R = 0.9 cm (defined at top)

            eyeInp = extrudes.createInput(
                skEye.profiles.item(0),
                adsk.fusion.FeatureOperations.CutFeatureOperation)
            # Symmetric cut: total = 2*(COVER_T + margin)
            # Covers full cover thickness (0.20 cm) from sketch plane with margin
            eyeInp.setSymmetricExtent(val(2.0 * (COVER_T + 0.10)), True)
            eyeInp.participantBodies = [coverBody]
            extrudes.add(eyeInp)
        else:
            ui.messageBox('Step 13 FAILED: FrontCover body not found!')

        # ════════════════════════════════════════
        #  STEP 13b: INLET PIPE
        #  Hollow cylindrical tube on top of FrontCover.
        #
        #  Geometry:
        #    Base Z  = HSG_H + COVER_T = 1.70 + 0.20 = 1.90 cm
        #             (flush with FrontCover top face)
        #    Length  = INLET_L = 2.00 cm  (20 mm)
        #    Top Z   = 1.90 + 2.00 = 3.90 cm
        #    Inner R = EYE_R      = 0.90 cm  (9 mm — matches eye hole exactly)
        #    Wall T  = PIPE_WALL  = 0.15 cm  (1.5 mm — same as volute wall)
        #    Outer R = EYE_R + PIPE_WALL = 1.05 cm  (10.5 mm)
        #
        #  Flow path:  Water enters at top (Z=3.90 cm),
        #              travels down through the pipe bore,
        #              exits through FrontCover eye into impeller.
        # ════════════════════════════════════════
        INLET_L   = 2.00   # 20 mm pipe length
        PIPE_WALL = 0.15   # 1.5 mm wall (same as volute wall)
        PIPE_OR   = EYE_R + PIPE_WALL   # 1.05 cm outer radius

        # Plane at Z = HSG_H + COVER_T (top face of FrontCover)
        inletPlaneIn = conPlanes.createInput()
        inletPlaneIn.setByOffset(xyPlane, val(HSG_H + COVER_T))
        inletPlane = conPlanes.add(inletPlaneIn)

        skInlet = sketches.add(inletPlane)
        skInlet.sketchCurves.sketchCircles.addByCenterRadius(
            pt(0, 0, 0), PIPE_OR)           # outer circle R = 1.05 cm
        skInlet.sketchCurves.sketchCircles.addByCenterRadius(
            pt(0, 0, 0), EYE_R)             # inner circle R = 0.90 cm (bore)

        # Select annular profile (2 profile loops = ring between circles)
        inletAnnular = None
        for pi in range(skInlet.profiles.count):
            p = skInlet.profiles.item(pi)
            if p.profileLoops.count == 2:
                inletAnnular = p
                break
        if inletAnnular is None and skInlet.profiles.count > 0:
            # Fallback: largest profile
            maxA = 0
            for pi in range(skInlet.profiles.count):
                p = skInlet.profiles.item(pi)
                a = p.areaProperties().area
                if a > maxA and p.profileLoops.count > 1:
                    maxA = a
                    inletAnnular = p
            if inletAnnular is None:
                inletAnnular = skInlet.profiles.item(0)

        if inletAnnular is not None:
            inletInp = extrudes.createInput(
                inletAnnular,
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            inletInp.setDistanceExtent(False, val(INLET_L))
            inletFeat = extrudes.add(inletInp)
            inletFeat.bodies.item(0).name = 'Inlet Pipe'
        else:
            ui.messageBox('Step 13b FAILED: Inlet Pipe annular profile not found!')

        # ════════════════════════════════════════
        #  STEP 14: BACK COVER PLATE

        #  Solid disc placed BELOW the housing (Z = −COVER_T → 0).
        #
        #  Symmetry proof (no HSG_H change needed):
        #    Back Cover top face    = Z =  0.00 cm  (xyPlane)
        #    Back Shroud bottom     = Z =  C  = 0.05 cm
        #    Gap (back, bottom)     = 0.05 cm = 0.5 mm = C  ✅
        #    Front Shroud top       = Z =  C + PLATE_T + BLADE_H + PLATE_T = 1.65 cm
        #    Housing top            = Z =  HSG_H = 1.70 cm
        #    Gap (front, top)       = 0.05 cm = 0.5 mm = C  ✅
        #
        #  R = HSG_R = 3.10 cm  (flush with housing wall)
        #  T = COVER_T = 0.20 cm  (same as FrontCover)
        # ════════════════════════════════════════
        backCoverPlaneIn = conPlanes.createInput()
        backCoverPlaneIn.setByOffset(xyPlane, val(-COVER_T))
        backCoverPlane = conPlanes.add(backCoverPlaneIn)

        skBCover = sketches.add(backCoverPlane)
        skBCover.sketchCurves.sketchCircles.addByCenterRadius(
            pt(0, 0, 0), HSG_R)

        bcInp = extrudes.createInput(
            skBCover.profiles.item(0),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        bcInp.setDistanceExtent(False, val(COVER_T))   # extrudes UP to Z = 0
        bcFeat = extrudes.add(bcInp)
        bcFeat.bodies.item(0).name = 'BackCover'

        # ════════════════════════════════════════
        #  STEP 15: SHAFT HOLE THROUGH BACK COVER
        #  R = SHAFT_R = 0.5 cm (5 mm).
        #  Aligns with the shaft hole cut in the Back Shroud (Step 10).
        #  Sketch on backCoverPlane (Z = −COVER_T = −0.20 cm).
        #  Symmetric cut total = 2*(COVER_T + 0.10) = 0.60 cm
        #    → each side = 0.30 cm from sketch plane
        #    → cuts from Z = −0.50 to Z = +0.10
        #    → back cover (Z = −0.20 to 0.00) fully cleared  ✅
        # ════════════════════════════════════════
        backCoverBody = None
        for bi in range(rootComp.bRepBodies.count):
            if rootComp.bRepBodies.item(bi).name == 'BackCover':
                backCoverBody = rootComp.bRepBodies.item(bi)
                break

        if backCoverBody is not None:
            skBCShaft = sketches.add(backCoverPlane)
            skBCShaft.sketchCurves.sketchCircles.addByCenterRadius(
                pt(0, 0, 0), SHAFT_R)

            bcShaftInp = extrudes.createInput(
                skBCShaft.profiles.item(0),
                adsk.fusion.FeatureOperations.CutFeatureOperation)
            bcShaftInp.setSymmetricExtent(val(2.0 * (COVER_T + 0.10)), True)
            bcShaftInp.participantBodies = [backCoverBody]
            extrudes.add(bcShaftInp)
        else:
            ui.messageBox('Step 15 FAILED: BackCover body not found!')

        # ════════════════════════════════════════
        #  STEP 15b: SHAFT BODY
        #
        #  A solid cylinder that extends 30 mm below the
        #  BackCover, showing the motor coupling point.
        #  Makes the CAD model look complete for presentation.
        #
        #  Geometry:
        #    R      = SHAFT_R = 0.50 cm  (5 mm = ∅10 mm)
        #    Bottom = Z = -(COVER_T + SHAFT_EXT) = -3.20 cm
        #    Top    = Z = 0.00 cm  (flush with BackCover top face)
        #    Passes through the BackCover shaft hole exactly.
        #
        #  For CFD in ANSYS:
        #    Shaft is BELOW the BackCover → outside fluid domain.
        #    Impact on flow simulation = ZERO.
        #    Simply assign its cylindrical surface as a
        #    Rotating Wall BC (ω = impeller speed, no-slip).
        # ════════════════════════════════════════
        SHAFT_EXT = 3.0   # 30 mm motor coupling below pump

        # Plane at shaft bottom: offset from backCoverPlane by -SHAFT_EXT
        # backCoverPlane is at Z = -COVER_T = -0.20 cm
        # → shaftBotPlane at Z = -0.20 - 3.0 = -3.20 cm
        shaftBotPlaneIn = conPlanes.createInput()
        shaftBotPlaneIn.setByOffset(backCoverPlane, val(-SHAFT_EXT))
        shaftBotPlane = conPlanes.add(shaftBotPlaneIn)

        skShaftBody = sketches.add(shaftBotPlane)
        skShaftBody.sketchCurves.sketchCircles.addByCenterRadius(
            pt(0, 0, 0), SHAFT_R)   # R = 0.50 cm (5 mm)

        # Extrude upward by (COVER_T + SHAFT_EXT) = 3.20 cm
        # → shaft top at Z = -3.20 + 3.20 = 0.00 cm  ✓
        shaftBodyInp = extrudes.createInput(
            skShaftBody.profiles.item(0),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        shaftBodyInp.setDistanceExtent(False, val(COVER_T + SHAFT_EXT))
        shaftBodyFeat = extrudes.add(shaftBodyInp)
        shaftBodyFeat.bodies.item(0).name = 'Shaft'

        # ════════════════════════════════════════
        #  STEP 16: FLOW-IMPROVEMENT FILLETS
        #
        #  WHY: Sharp 90° edges cause flow separation — the fluid
        #  detaches from the wall and forms a recirculation bubble
        #  that wastes energy and reduces effective flow area.
        #
        #  Two locations targeted (both on internal flow path):
        #
        #  A) FrontCover suction inlet edge
        #     Location: R = EYE_R = 0.9 cm, Z = HSG_H (entry face)
        #     Effect:   Eliminates vena contracta at pump inlet
        #               → smoother acceleration of fluid into impeller eye
        #
        #  B) Casing bore mouth edges (top AND bottom)
        #     Location: R = CUTWATER_R = 2.90 cm, Z ≈ 0 and Z ≈ HSG_H
        #     Effect:   Smooths impeller tip discharge into volute entry
        #               → reduces turbulence at the 2.9 cm annular gap
        #
        #  Fillet radius: 0.5 mm (0.05 cm) — minimum effective for CFD,
        #  small enough not to alter the structural geometry.
        #
        #  All ops wrapped in try/except — fillet may fail on complex
        #  boolean geometry without affecting the rest of the model.
        # ════════════════════════════════════════
        FILLET_R = 0.05   # 0.5 mm fillet radius

        # ── 16a: FrontCover suction inlet edge ──────────────────
        try:
            coverBodyF = None
            for bi in range(rootComp.bRepBodies.count):
                if rootComp.bRepBodies.item(bi).name == 'FrontCover':
                    coverBodyF = rootComp.bRepBodies.item(bi)
                    break

            if coverBodyF is not None:
                eyeEdges = adsk.core.ObjectCollection.create()
                for ei in range(coverBodyF.edges.count):
                    eg = coverBodyF.edges.item(ei)
                    geom = eg.geometry
                    # Circular edge with radius ≈ EYE_R at the inner inlet face
                    if geom.objectType == adsk.core.Circle3D.classType():
                        if abs(geom.radius - EYE_R) < 0.02:
                            eyeEdges.add(eg)

                if eyeEdges.count > 0:
                    fi1 = rootComp.features.filletFeatures.createInput()
                    fi1.addConstantRadiusEdgeSet(
                        eyeEdges, val(FILLET_R), True)
                    rootComp.features.filletFeatures.add(fi1)
        except:
            pass  # fillet skipped — model is still valid

        # ── 16b: Casing bore mouth edges (top & bottom) ─────────
        try:
            casingBodyF = None
            for bi in range(rootComp.bRepBodies.count):
                if rootComp.bRepBodies.item(bi).name == 'Casing':
                    casingBodyF = rootComp.bRepBodies.item(bi)
                    break

            if casingBodyF is not None:
                boreEdges = adsk.core.ObjectCollection.create()
                for ei in range(casingBodyF.edges.count):
                    eg = casingBodyF.edges.item(ei)
                    geom = eg.geometry
                    # Circular edge with radius ≈ CUTWATER_R
                    if geom.objectType == adsk.core.Circle3D.classType():
                        if abs(geom.radius - CUTWATER_R) < 0.05:
                            # Only at bore mouth: Z ≈ 0 (bottom) or Z ≈ HSG_H (top)
                            p = eg.pointOnEdge
                            at_bottom = abs(p.z) < 0.10
                            at_top    = abs(p.z - HSG_H) < 0.10
                            if at_bottom or at_top:
                                boreEdges.add(eg)

                if boreEdges.count > 0:
                    fi2 = rootComp.features.filletFeatures.createInput()
                    fi2.addConstantRadiusEdgeSet(
                        boreEdges, val(FILLET_R), True)
                    rootComp.features.filletFeatures.add(fi2)
        except:
            pass  # fillet skipped — model is still valid

        # ════════════════════════════════════════
        #  DONE
        # ════════════════════════════════════════


        try:
            app.activeViewport.fit()
        except:
            pass

        # Export
        try:
            desk = os.path.expanduser('~/Desktop')
            sf = os.path.join(desk, 'NITK_Centrifugal_Pump.step')
            m = design.exportManager
            o = m.createSTEPExportOptions(sf, rootComp)
            m.execute(o)
            exp = 'STEP: ' + sf
        except:
            exp = 'Export failed — use File > Export'

        names = []
        for i in range(rootComp.bRepBodies.count):
            names.append(rootComp.bRepBodies.item(i).name)

        ui.messageBox(
            'NITK Centrifugal Pump v6 — Complete!\n\n'
            'Bodies ({}):\n'.format(len(names)) +
            '\n'.join(['  {} - {}'.format(i+1, n)
                       for i, n in enumerate(names)]) +
            '\n\nExpected (6): Impeller, Casing, FrontCover, Inlet Pipe, BackCover, Shaft'
            '\n\n' + exp,
            'Done!')

    except:
        if ui:
            ui.messageBox('FAILED:\n{}'.format(traceback.format_exc()))
