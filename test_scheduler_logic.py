from scheduler_logic import create_empty_schedule, add_fixed_event, add_unfixed_event, get_schedule

def test_add_fixed_event() -> None:
    """
    Verifies that adding a valid fixed event succeeds, fills the correct slots,
    and leaves the slot immediately after end_hour untouched (end_hour is exclusive).
    """
    schedule = create_empty_schedule()
    result = add_fixed_event(schedule, 9, 11, "Work")
    assert result[0] is True
    assert schedule[9] == "Work"
    assert schedule[10] == "Work"
    assert schedule[11] is None

def test_create_empty_schedule() -> None:
    """
    Verifies that create_empty_schedule() returns a list of exactly 24 None slots.
    Every slot must be None — no slot is pre-filled.
    """
    schedule = create_empty_schedule()
    assert len(schedule) == 24
    assert all(slot is None for slot in schedule)

def test_add_fixed_event_overlap_rejected() -> None:
    """
    Verifies that adding an overlapping event is rejected without corrupting the schedule.
    The implementation checks all slots before writing any, so a partial write cannot occur:
    - The existing event ("Sleep", slots 0-7) must remain fully intact.
    - The slots outside the existing event that the new event would have claimed (slot 8, 9)
      must remain None.
    """
    schedule = create_empty_schedule()
    add_fixed_event(schedule, 0, 8, "Sleep")  # fills slots 0-7

    result = add_fixed_event(schedule, 6, 10, "Work")  # overlaps slots 6 and 7
    assert result[0] is False

    # Existing event must be untouched.
    assert all(schedule[i] == "Sleep" for i in range(0, 8))
    # Slots the rejected event would have written must still be free.
    assert schedule[8] is None
    assert schedule[9] is None

def test_add_fixed_event_invalid_ranges() -> None:
    """
    Verifies that add_fixed_event() rejects invalid time ranges:
    - Zero-duration event (start == end) is rejected.
    - Reversed range (end before start) is rejected.
    - end_hour greater than 24 is out of range and is rejected.
    In all cases, the schedule must remain completely empty.
    """
    # Zero-duration: start equals end.
    schedule = create_empty_schedule()
    result = add_fixed_event(schedule, 5, 5, "Task")
    assert result[0] is False
    assert all(slot is None for slot in schedule)

    # Reversed: end is before start.
    schedule = create_empty_schedule()
    result = add_fixed_event(schedule, 5, 3, "Task")
    assert result[0] is False
    assert all(slot is None for slot in schedule)

    # end_hour out of range: valid range is 1-24, so 25 must be rejected.
    schedule = create_empty_schedule()
    result = add_fixed_event(schedule, 0, 25, "Task")
    assert result[0] is False
    assert all(slot is None for slot in schedule)

def test_add_unfixed_event_uses_first_consecutive_block() -> None:
    """
    Verifies that add_unfixed_event() places the task in the earliest consecutive
    free block of sufficient length, not scattered across isolated free slots.
    Setup: slots 0-5 are occupied ("Sleep"), leaving slots 6-23 as one large free block.
    A 3-hour task should land on slots 6, 7, 8 — the start of the first eligible block.
    """
    schedule = create_empty_schedule()
    add_fixed_event(schedule, 0, 6, "Sleep")  # fills slots 0-5

    result = add_unfixed_event(schedule, 3, "Study")
    assert result[0] is True
    assert schedule[6] == "Study"
    assert schedule[7] == "Study"
    assert schedule[8] == "Study"
    # The slot just after the placed block must still be free.
    assert schedule[9] is None

def test_add_unfixed_event_scatter_fallback() -> None:
    """
    Verifies the scatter fallback: when free slots exist but no single consecutive
    block is long enough, add_unfixed_event() fills the earliest available free
    slots one by one and still returns True.

    Setup: every even hour is occupied ("Busy"), every odd hour is free —
    giving 12 free slots, all isolated (no two consecutive free slots).
    Requesting 3 hours forces the scatter path. The first three free slots
    are hours 1, 3, and 5, so those must contain the task name.
    """
    schedule = create_empty_schedule()
    for i in range(0, 24, 2):   # occupy every even slot: 0, 2, 4, ..., 22
        schedule[i] = "Busy"
    # Free slots are now: 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23 (all isolated)

    result = add_unfixed_event(schedule, 3, "Study")
    assert result[0] is True
    assert schedule[1] == "Study"
    assert schedule[3] == "Study"
    assert schedule[5] == "Study"
    # Slots beyond the first 3 free slots must be unaffected.
    assert schedule[7] is None

def test_add_unfixed_event_insufficient_capacity() -> None:
    """
    Verifies that add_unfixed_event() is rejected when total free slots are fewer
    than the requested hours_count, and that the schedule is not modified.
    Setup: only 1 slot is free (slot 10); requesting 2 hours must fail.
    """
    schedule = create_empty_schedule()
    for i in range(24):
        if i != 10:
            schedule[i] = "Busy"  # leaves only slot 10 free

    result = add_unfixed_event(schedule, 2, "Study")
    assert result[0] is False
    # The single free slot must remain untouched.
    assert schedule[10] is None

def test_get_schedule_groups_and_formats_correctly() -> None:
    """
    Verifies that get_schedule() groups consecutive identical slots, formats
    task names in bold (*name*), and labels free hours as _שעה פנויה_.
    Setup: "Sleep" fills slots 0-7 (end_hour=8, exclusive), slots 8-23 are free.
    Expected: exactly two lines after the header — one for Sleep, one for free time.
    The last block always ends at 24 (hard-coded in the implementation).
    """
    schedule = create_empty_schedule()
    add_fixed_event(schedule, 0, 8, "Sleep")  # fills slots 0-7

    output = get_schedule(schedule)

    assert output.startswith("📅 *הלוח היומי שלך:*")
    assert "⏰ 00:00 - 08:00 : *Sleep*" in output
    assert "⏰ 08:00 - 24:00 : _שעה פנויה_" in output