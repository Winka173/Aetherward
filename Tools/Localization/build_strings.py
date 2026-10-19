#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Builds Resources/Content/loc_en.json and loc_vi.json from the authored tables.
Run from repo root: python3 Tools/Localization/build_strings.py"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strings_content import (HEROES, EVOLUTIONS, EVO_PASSIVES, ENEMIES, AFFIXES, REACTIONS, RELICS, CARDS, CARD_DRAWBACKS,
                             EVENTS, WAVES, LANES)
import strings_expansion as X

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "Assets", "_Aetherward", "Resources", "Content")

UI = {
    # --- general
    "game.title": ("AETHERWARD", "AETHERWARD"),
    "game.tagline": ("Guard the Crystal. Weave the elements.", "Bảo vệ Pha Lê. Dệt nên nguyên tố."),
    "common.continue": ("Continue", "Tiếp tục"), "common.back": ("Back", "Quay lại"), "common.close": ("Close", "Đóng"),
    "common.confirm": ("Confirm", "Xác nhận"), "common.cancel": ("Cancel", "Huỷ"), "common.skip": ("Skip", "Bỏ qua"),
    "common.done": ("Done", "Xong"), "common.yes": ("Yes", "Có"), "common.no": ("No", "Không"), "common.locked": ("Locked", "Chưa mở"),
    "common.level": ("Lv {0}", "Cấp {0}"), "common.gold": ("Gold", "Vàng"), "common.essence": ("Essence", "Tinh Chất"),
    "common.free": ("Free", "Miễn phí"), "common.sold": ("Sold", "Đã bán"), "common.cost": ("{0} Gold", "{0} Vàng"),
    "common.seconds": ("{0}s", "{0}s"), "common.loading": ("Loading…", "Đang tải…"), "common.unknown": ("???", "???"),
    "common.wave": ("Wave {0}/{1}", "Đợt {0}/{1}"), "common.seed": ("Seed {0}", "Seed {0}"),
    # --- main menu
    "menu.new_run": ("New Run", "Lượt mới"), "menu.continue": ("Continue Run", "Chơi tiếp"), "menu.codex": ("Codex", "Bách khoa"),
    "menu.history": ("Run History", "Lịch sử"), "menu.settings": ("Settings", "Cài đặt"), "menu.quit": ("Quit", "Thoát"),
    "menu.stats": ("Runs {0} · Victories {1} · Best wave {2}", "Số lượt {0} · Chiến thắng {1} · Đợt cao nhất {2}"),
    "menu.save_reset": ("Your save could not be read and was reset to a clean profile.", "Không đọc được dữ liệu lưu, hồ sơ đã được làm mới."),
    "menu.version": ("Version {0}", "Phiên bản {0}"),
    # --- team select
    "team.title": ("Choose two starting heroes", "Chọn hai anh hùng khởi đầu"),
    "team.subtitle": ("You can recruit up to 6 heroes during the run.", "Có thể chiêu mộ tối đa 6 anh hùng trong lượt chơi."),
    "team.start": ("Begin Defense", "Bắt đầu phòng thủ"), "team.random_seed": ("Random seed", "Seed ngẫu nhiên"),
    "team.ascension": ("Ascension {0}", "Thăng cấp {0}"), "team.ascension_none": ("Normal", "Thường"),
    "team.ascension_desc.0": ("Standard difficulty.", "Độ khó tiêu chuẩn."),
    "team.ascension_desc.1": ("Enemies move 10% faster.", "Kẻ địch nhanh hơn 10%."),
    "team.ascension_desc.2": ("+ Enemies +8% more speed; shop prices +15%.", "+ Kẻ địch thêm 8% tốc độ; giá cửa hàng +15%."),
    "team.ascension_desc.3": ("+ Crystal starts with 15% less max HP; one defense node is blocked each wave (shown in preparation).", "+ Pha Lê bắt đầu với ít hơn 15% HP tối đa; mỗi đợt một ô phòng thủ bị khoá (hiện khi chuẩn bị)."),
    "team.ascension_desc.4": ("+ Enemies deal 10% more damage; elites carry an affix.", "+ Kẻ địch gây thêm 10% sát thương; elite mang thêm thuộc tính."),
    "team.ascension_desc.5": ("+ Bosses enrage below 25% HP (+25% damage). Enemy HP scales 8% per level.", "+ Boss nổi giận khi dưới 25% HP (+25% sát thương). HP kẻ địch tăng 8% mỗi cấp."),
    "team.locked_hint": ("Unlock: {0}", "Mở khoá: {0}"),
    "team.pick_two": ("Pick two heroes", "Hãy chọn hai anh hùng"),
    # --- unlock conditions
    "unlock.reach_wave": ("reach wave {0}", "đạt đợt {0}"), "unlock.total_reactions": ("trigger {0} reactions in total", "gây tổng cộng {0} phản ứng"),
    "unlock.distinct_reactions": ("discover {0} different reactions", "khám phá {0} loại phản ứng"),
    "unlock.defeat_boss": ("defeat {0}", "hạ {0}"), "unlock.hero_runs": ("play {0} runs", "chơi {0} lượt"),
    "unlock.victory": ("win a run", "thắng một lượt"),
    # --- HUD
    "hud.crystal": ("Crystal", "Pha Lê"), "hud.wave": ("WAVE {0}", "ĐỢT {0}"), "hud.enemies": ("Enemies {0}", "Kẻ địch {0}"),
    "hud.speed": ("{0}×", "{0}×"), "hud.pause": ("Pause", "Tạm dừng"), "hud.vfx_reduced": ("Reduced VFX", "Giảm hiệu ứng"),
    "hud.ready": ("READY", "SẴN SÀNG"), "hud.downed": ("DOWN", "GỤC"), "hud.boss": ("{0}", "{0}"),
    "hud.wave_start": ("Wave {0}: {1}", "Đợt {0}: {1}"), "hud.wave_clear": ("Wave cleared!", "Đã giữ vững đợt!"),
    "hud.timeout": ("Time's up! Remaining enemies breach the Crystal.", "Hết giờ! Kẻ địch còn lại tấn công Pha Lê."),
    "hud.boss_phase": ("Phase {0}", "Pha {0}"), "hud.exposed": ("EXPOSED!", "LỘ SƠ HỞ!"), "hud.armor_up": ("ARMOR UP", "GIÁP DÀY"),
    "hud.armor_down": ("ARMOR BROKEN", "GIÁP VỠ"), "hud.lane_marked": ("Lane marked: {0}!", "Làn bị đánh dấu: {0}!"),
    "hud.combo": ("{0} reactions!", "{0} phản ứng!"),
    # --- preparation
    "prep.title": ("Prepare: Wave {0}", "Chuẩn bị: Đợt {0}"), "prep.start": ("Start Wave", "Bắt đầu đợt"),
    "prep.auto": ("Auto Arrange", "Tự sắp xếp"), "prep.revive": ("Revive ({0})", "Hồi sinh ({0})"), "prep.repair": ("Repair Crystal ({0})", "Sửa Pha Lê ({0})"),
    "prep.evolve": ("Evolve", "Tiến hoá"), "prep.build": ("Build", "Đội hình"), "prep.incoming": ("Incoming", "Sắp tới"),
    "prep.lanes": ("Lanes: {0}", "Làn: {0}"), "prep.drag_hint": ("Drag heroes onto glowing nodes (or tap a hero, then a node). Swapping is free.",
                                                               "Kéo anh hùng vào các ô phát sáng (hoặc chạm anh hùng rồi chạm ô). Đổi chỗ miễn phí."),
    "prep.downed_hint": ("{0} is down. Revive for {1} Gold or leave the node empty.", "{0} đã gục. Hồi sinh với {1} Vàng hoặc để trống."),
    "prep.evolve_ready": ("{0} can evolve!", "{0} có thể tiến hoá!"),
    "prep.relics": ("Relics", "Di vật"), "prep.cards": ("Upgrades", "Nâng cấp"), "prep.none": ("None yet", "Chưa có"),
    "prep.xp": ("XP {0}/{1}", "KN {0}/{1}"), "prep.max_level": ("Max level", "Cấp tối đa"),
    # --- rewards
    "reward.draft": ("Choose an upgrade", "Chọn một nâng cấp"), "reward.recruit": ("Recruit a hero", "Chiêu mộ anh hùng"),
    "reward.shop": ("Rift Shop", "Cửa hàng Khe Nứt"), "reward.relic": ("Choose a relic", "Chọn một di vật"),
    "reward.evolution": ("Evolution", "Tiến hoá"), "reward.event": ("Event", "Sự kiện"), "reward.pact": ("A Cursed Pact", "Khế ước bị nguyền"),
    "reward.reroll": ("Reroll ({0})", "Đổi ({0})"), "reward.reroll_free": ("Reroll (free)", "Đổi (miễn phí)"),
    "reward.take": ("Take", "Nhận"), "reward.buy": ("Buy", "Mua"), "reward.recruit_btn": ("Recruit", "Chiêu mộ"),
    "reward.leave": ("Leave", "Rời đi"), "reward.decline": ("Decline", "Từ chối"), "reward.accept": ("Accept", "Chấp nhận"),
    "reward.not_enough": ("Not enough Gold", "Không đủ Vàng"), "reward.roster_full": ("Roster full (6/6)", "Đội đã đủ (6/6)"),
    "reward.fusion_hint": ("Completes a fusion!", "Hoàn thành hợp thể!"), "reward.synergy": ("Synergy", "Cộng hưởng"),
    "reward.specialization": ("Specialization", "Chuyên môn"), "reward.pivot": ("Rule change", "Đổi luật"), "reward.cursed": ("Cursed", "Bị nguyền"),
    "reward.stacks": ("Owned {0}/{1}", "Đang có {0}/{1}"), "reward.evolve_cost": ("{0} Essence", "{0} Tinh Chất"),
    "reward.evo_choose": ("Choose a path for {0}", "Chọn con đường cho {0}"), "reward.evo_none": ("No hero is ready to evolve.", "Chưa có anh hùng sẵn sàng tiến hoá."),
    "reward.pact_confirm": ("Accept this pact? The drawback lasts for the rest of the run.", "Chấp nhận khế ước? Bất lợi kéo dài đến hết lượt chơi."),
    "reward.repair": ("Repair Crystal +{0}%", "Sửa Pha Lê +{0}%"), "reward.revive": ("Revive {0}", "Hồi sinh {0}"),
    "reward.save_gold": ("Unspent Gold earns interest: +1 per 10 (max {0}).", "Vàng chưa tiêu sinh lãi: +1 mỗi 10 (tối đa {0})."),
    "reward.hero_level": ("Joins at level {0}", "Gia nhập ở cấp {0}"),
    "reward.next": ("Next", "Tiếp"),
    # --- pause
    "pause.title": ("Paused", "Tạm dừng"), "pause.resume": ("Resume", "Tiếp tục"), "pause.abandon": ("Abandon Run", "Bỏ lượt chơi"),
    "pause.abandon_confirm": ("Abandon this run? It will count as a defeat.", "Bỏ lượt này? Sẽ tính là thất bại."),
    "pause.to_menu": ("Save & Quit to Menu", "Lưu và về menu"),
    "pause.save_note": ("Runs are saved between waves. Quitting mid-wave restarts that wave.", "Lượt chơi được lưu giữa các đợt. Thoát giữa đợt sẽ chơi lại đợt đó."),
    # --- results
    "results.victory": ("VICTORY", "CHIẾN THẮNG"), "results.defeat": ("DEFEAT", "THẤT BẠI"),
    "results.reached": ("Reached wave {0} · {1} active", "Đạt đợt {0} · {1} chiến đấu"),
    "results.heroes": ("Heroes", "Anh hùng"), "results.reactions": ("Reactions", "Phản ứng"), "results.relics": ("Relic activations", "Kích hoạt di vật"),
    "results.insights": ("Why it went this way", "Vì sao kết quả như vậy"), "results.unlocked": ("Unlocked!", "Đã mở khoá!"),
    "results.replay": ("New Run (new seed)", "Lượt mới (seed mới)"), "results.menu": ("Main Menu", "Menu chính"),
    "results.damage": ("Damage", "Sát thương"), "results.healing": ("Healing", "Hồi máu"), "results.kills": ("Kills", "Hạ gục"),
    "results.mvp": ("MVP", "MVP"), "results.crystal": ("Crystal HP by wave", "HP Pha Lê theo đợt"), "results.elements": ("Damage by element", "Sát thương theo nguyên tố"),
    "results.build": ("Build", "Lối chơi"), "results.seed": ("Seed {0} · v{1}", "Seed {0} · v{1}"),
    # --- insights (key|arg)
    "insight.reaction_engine": ("Reactions dealt {0}% of all damage: a true reaction engine.", "Phản ứng gây {0}% tổng sát thương: một cỗ máy phản ứng thực thụ."),
    "insight.strongest_reaction": ("Strongest reaction: {0}.", "Phản ứng mạnh nhất: {0}."),
    "insight.worst_wave": ("Wave {0} hurt the Crystal the most.", "Đợt {0} gây hại cho Pha Lê nhiều nhất."),
    "insight.many_leaks": ("{0} enemies reached the Crystal. Guard the lanes closer to the center.", "{0} kẻ địch chạm tới Pha Lê. Hãy giữ làn gần trung tâm hơn."),
    "insight.fragile_team": ("Heroes went down {0} times. More defense or healing would help.", "Anh hùng gục {0} lần. Cần thêm phòng thủ hoặc hồi máu."),
    "insight.defeated_by": ("Most crystal damage came from: {0}.", "Sát thương lên Pha Lê chủ yếu từ: {0}."),
    "insight.small_roster": ("Only {0} heroes: recruiting earlier adds coverage.", "Chỉ có {0} anh hùng: chiêu mộ sớm hơn giúp bao quát tốt hơn."),
    # --- notices
    "notice.level_up": ("Level up!", "Lên cấp!"), "notice.evolved": ("Evolved!", "Đã tiến hoá!"), "notice.fusion": ("Relics fused!", "Di vật hợp thể!"),
    # --- codex
    "codex.title": ("Codex", "Bách khoa"), "codex.heroes": ("Heroes", "Anh hùng"), "codex.reactions": ("Reactions", "Phản ứng"),
    "codex.relics": ("Relics", "Di vật"), "codex.enemies": ("Enemies", "Kẻ địch"), "codex.undiscovered": ("Undiscovered", "Chưa khám phá"),
    "codex.progress": ("Discovered {0}/{1}", "Đã khám phá {0}/{1}"), "codex.evolutions": ("Evolutions", "Tiến hoá"),
    "codex.reaction_formula": ("Reaction power = base × wave level + Attack × scale, boosted by Elemental Mastery and reaction bonuses. Reactions ignore Defense but not resistance. Each pair has a short per-target cooldown and chains stop after 2 generations.",
                               "Sức mạnh phản ứng = gốc × cấp đợt + Công × hệ số, tăng theo Tinh Thông Nguyên Tố và thưởng phản ứng. Phản ứng bỏ qua Thủ nhưng không bỏ qua kháng. Mỗi cặp có hồi chiêu ngắn trên từng mục tiêu và chuỗi dừng sau 2 tầng."),
    # --- history
    "history.title": ("Run History", "Lịch sử"), "history.empty": ("No runs yet.", "Chưa có lượt nào."),
    "history.row": ("{0} · Wave {1} · {2} reactions · MVP {3}", "{0} · Đợt {1} · {2} phản ứng · MVP {3}"),
    # --- settings
    "settings.title": ("Settings", "Cài đặt"), "settings.language": ("Language", "Ngôn ngữ"), "settings.master": ("Master volume", "Âm lượng tổng"),
    "settings.music": ("Music", "Nhạc"), "settings.sfx": ("Effects", "Hiệu ứng âm"), "settings.ui": ("Interface", "Giao diện"),
    "settings.fast": ("Start waves at 2× speed", "Bắt đầu đợt ở tốc độ 2×"), "settings.reduced_vfx": ("Reduced visual effects", "Giảm hiệu ứng hình ảnh"),
    "settings.shake": ("Screen shake", "Rung màn hình"), "settings.numbers": ("Damage numbers", "Số sát thương"),
    "settings.contrast": ("High contrast", "Tương phản cao"), "settings.fps": ("Target FPS", "FPS mục tiêu"), "settings.ranges": ("Show ranges (debug)", "Hiện tầm đánh (debug)"),
    "settings.on": ("On", "Bật"), "settings.off": ("Off", "Tắt"), "lang.en": ("English", "English"), "lang.vi": ("Tiếng Việt", "Tiếng Việt"),
    # --- tutorial
    "tutorial.1": ("Your heroes defend the Crystal automatically. Watch them fight!", "Anh hùng tự động bảo vệ Pha Lê. Hãy xem họ chiến đấu!"),
    "tutorial.2": ("Between waves, drag heroes to nodes near the red lane arrows.", "Giữa các đợt, kéo anh hùng tới các ô gần mũi tên đỏ."),
    "tutorial.3": ("Different elements combine into reactions. Mix your team!", "Các nguyên tố khác nhau kết hợp thành phản ứng. Hãy phối hợp đội hình!"),
    "tutorial.4": ("Use 2× speed when the wave is under control.", "Dùng tốc độ 2× khi đã kiểm soát được trận đấu."),
    # --- tooltip effect lines
    "fx.attack_speed": ("{0}% attack speed", "{0}% tốc đánh"), "fx.skill_haste": ("{0}% skill haste (shorter cooldowns)", "{0}% hồi chiêu nhanh hơn"),
    "fx.stat_pct": ("{0}% {1}", "{0}% {1}"), "fx.stat_flat": ("{0} {1}", "{0} {1}"),
    "fx.scope.hero": (" ({0})", " ({0})"), "fx.scope.element": (" ({0} heroes)", " (anh hùng {0})"), "fx.scope.role": (" ({0}s)", " ({0})"),
    "fx.scope.melee": (" (melee heroes)", " (anh hùng cận chiến)"), "fx.scope.ranged": (" (ranged heroes)", " (anh hùng đánh xa)"),
    "fx.crystal_max_hp": ("{0}% Crystal max HP", "{0}% HP tối đa của Pha Lê"), "fx.crystal_max_hp_flat": ("{0} Crystal max HP", "{0} HP tối đa của Pha Lê"),
    "fx.crystal_reduction": ("Crystal takes {0}% less damage", "Pha Lê nhận ít hơn {0}% sát thương"),
    "fx.crystal_regen": ("Crystal regenerates {0} HP/s", "Pha Lê hồi {0} HP/giây"),
    "fx.crystal_thorns": ("Enemies hitting the Crystal take {0} Earth damage (scales with wave)", "Kẻ đánh Pha Lê nhận {0} sát thương Đất (tăng theo đợt)"),
    "fx.enemy_hp": ("Enemies {0}% HP", "Kẻ địch {0}% HP"), "fx.enemy_speed": ("Enemies {0}% speed", "Kẻ địch {0}% tốc độ"),
    "fx.enemy_damage": ("Enemies {0}% damage", "Kẻ địch {0}% sát thương"), "fx.enemy_gold": ("{0}% Gold from kills", "{0}% Vàng khi hạ địch"),
    "fx.reaction_damage": ("{0}: {1}% damage", "{0}: {1}% sát thương"), "fx.reaction_radius": ("{0}: {1}% area", "{0}: {1}% diện tích"),
    "fx.reaction_duration": ("{0}: {1}% duration", "{0}: {1}% thời gian"), "fx.reaction_bounces": ("{0}: {1} bounces", "{0}: {1} lần nảy"),
    "fx.reaction_status": ("{0}: {1}% control strength", "{0}: {1}% sức khống chế"), "fx.all_reactions": ("All reactions", "Mọi phản ứng"),
    "fx.all_elements": ("all elements", "mọi nguyên tố"), "fx.gauge": ("{0}% {1} application", "{0}% lượng {1} áp lên"),
    "fx.healing": ("{0}% healing", "{0}% hồi phục"), "fx.gold_pct": ("{0}% Gold earned", "{0}% Vàng nhận được"),
    "fx.wave_gold": ("{0} Gold per wave", "{0} Vàng mỗi đợt"), "fx.interest_cap": ("{0} maximum interest per wave", "{0} lãi tối đa mỗi đợt"),
    "fx.xp_bonus": ("{0} XP per wave for every hero", "{0} KN mỗi đợt cho mọi anh hùng"), "fx.essence_elite": ("{0} Essence after elite and boss waves", "{0} Tinh Chất sau đợt elite và boss"),
    "fx.shop_discount": ("Shop prices -{0}%", "Giá cửa hàng -{0}%"), "fx.free_rerolls": ("{0} free reroll(s) per screen", "{0} lượt đổi miễn phí mỗi màn"),
    "fx.revive_discount": ("Revives cost {0}% less", "Hồi sinh rẻ hơn {0}%"),
    "fx.rule.mirror_reactions": ("Reactions also apply the consumed element to one nearby enemy", "Phản ứng còn áp nguyên tố bị tiêu hao lên một kẻ địch gần đó"),
    "fx.rule.burn_power": ("Burn deals {0}% more damage", "Bỏng gây thêm {0}% sát thương"),
    "fx.rule.lingering_elements": ("Leftover element gauge stays after reactions", "Lượng nguyên tố dư còn lại sau phản ứng"),
    "fx.rule.proc_generation_bonus": ("Reaction chains can go {0} generation deeper", "Chuỗi phản ứng sâu thêm {0} tầng"),
    "fx.rule.overheal_shield": ("{0}% of overhealing becomes a shield", "{0}% lượng hồi dư thành khiên"),
    "fx.rule.no_healing": ("All healing is halved", "Mọi hồi phục giảm một nửa"),
    "fx.skill": ("{0}: {1} {2}", "{0}: {1} {2}"), "fx.card": ("Gain upgrade: {0}", "Nhận nâng cấp: {0}"), "fx.physical": ("physical", "vật lý"),
    "fx.on.skill_cast": ("When a hero casts a skill", "Khi anh hùng dùng kỹ năng"), "fx.on.basic_attack": ("On basic attack", "Khi đánh thường"),
    "fx.on.kill": ("On kill", "Khi hạ địch"), "fx.on.crit": ("On critical hit", "Khi chí mạng"), "fx.on.wave_start": ("At wave start", "Khi bắt đầu đợt"),
    "fx.on.crystal_hit": ("When the Crystal is hit", "Khi Pha Lê bị đánh"), "fx.on.hero_downed": ("When a hero would fall", "Khi một anh hùng sắp gục"),
    "fx.on.reaction": ("When {0} triggers", "Khi {0} kích hoạt"), "fx.on.periodic": ("Every {0}s", "Mỗi {0}s"),
    "fx.filter.element": (" ({0} heroes)", " (anh hùng {0})"), "fx.every": ("every {0}th time", "mỗi lần thứ {0}"), "fx.chance": ("{0}% chance", "{0}% cơ hội"),
    "fx.cooldown": (" ({0}s cooldown)", " (hồi {0}s)"), "fx.uses": (" ({0}× per wave)", " ({0} lần mỗi đợt)"),
    "fx.do.burst": ("deal {0}% Attack as {1} damage in {2} m", "gây {0}% Công sát thương {1} trong {2} m"),
    "fx.do.apply_element": ("apply {0} to enemies within {1} m", "áp {0} lên kẻ địch trong {1} m"),
    "fx.do.chain": ("lightning arcs to {0} more enemies", "sét lan sang {0} kẻ địch khác"),
    "fx.do.heal_team": ("heal all heroes for {0}% max HP", "hồi cho mọi anh hùng {0}% HP tối đa"),
    "fx.do.crystal_shield": ("shield the Crystal for {0}% of its max HP", "tạo khiên cho Pha Lê bằng {0}% HP tối đa"),
    "fx.do.crystal_heal": ("heal the Crystal for {0}% of its max HP", "hồi cho Pha Lê {0}% HP tối đa"),
    "fx.do.gold": ("gain {0} Gold", "nhận {0} Vàng"), "fx.do.team_buff": ("all heroes gain {0}% {1} for {2}s", "mọi anh hùng +{0}% {1} trong {2}s"),
    "fx.do.hero_buff": ("that hero gains {0}% {1} for {2}s", "anh hùng đó +{0}% {1} trong {2}s"),
    "fx.do.revive": ("they stand back up with {0}% HP", "họ đứng dậy với {0}% HP"),
    "fx.do.zone": ("leave {0} ({1} m, {2}s)", "để lại {0} ({1} m, {2}s)"), "fx.do.refund_cooldown": ("that skill recharges {0}s faster", "kỹ năng đó hồi nhanh hơn {0}s"),
    "fx.do.team_refund_cooldown": ("all skills recharge {0}s faster", "mọi kỹ năng hồi nhanh hơn {0}s"),
    "fx.do.echo_cast": ("recast it at {0}% power", "thi triển lại với {0}% sức mạnh"),
    "fx.do.execute": ("execute non-boss enemies below {0}% HP", "kết liễu kẻ địch thường dưới {0}% HP"),
    "fx.do.slow_all": ("slow enemies within {0} m by {1}% for {2}s", "làm chậm kẻ địch trong {0} m {1}% trong {2}s"),
    # --- skill params (specialization tooltips)
    "skillparam.radius": ("area", "bán kính"), "skillparam.burnSpread": ("Burn spread radius", "bán kính lan Bỏng"), "skillparam.arc": ("cleave arc (°)", "cung chém (°)"),
    "skillparam.groundDuration": ("burning ground (s)", "đất cháy (s)"), "skillparam.duration": ("duration (s)", "thời gian (s)"),
    "skillparam.knock": ("knockback (m)", "đẩy lùi (m)"), "skillparam.length": ("wave length (m)", "độ dài sóng (m)"), "skillparam.jumps": ("jumps", "số lần nhảy"),
    "skillparam.jumpRange": ("jump range (m)", "tầm nhảy (m)"), "skillparam.trailDuration": ("storm trail (s)", "vệt bão (s)"),
    "skillparam.trailPower": ("trail power", "sức mạnh vệt bão"), "skillparam.zoneDuration": ("blizzard (s)", "bão tuyết (s)"),
    "skillparam.zonePower": ("blizzard power", "sức mạnh bão tuyết"), "skillparam.allyShieldPct": ("ally shield", "khiên đồng minh"),
    "skillparam.allyRadius": ("ally shield radius (m)", "bán kính khiên đồng minh (m)"), "skillparam.arrows": ("arrows", "số mũi tên"),
    "skillparam.spread": ("spread (°)", "độ toả (°)"), "skillparam.crystalReduction": ("Crystal damage reduction", "giảm sát thương lên Pha Lê"),
    "skillparam.taunt": ("taunt (s)", "khiêu khích (s)"), "skillparam.aftershock": ("aftershock", "dư chấn"), "skillparam.crackMax": ("max Armor Crack stacks", "tầng Nứt Giáp tối đa"),
    # --- zones / statuses
    "zone.burning_ground": ("burning ground", "đất cháy"), "zone.tempest_link": ("an electric field", "trường điện"), "zone.magma": ("magma", "dung nham"),
    "status.burn": ("Burning", "Bỏng"), "status.wet": ("Wet", "Ướt"), "status.charged": ("Charged", "Tích Điện"), "status.chill": ("Chilled", "Lạnh"),
    "status.windmark": ("Wind Mark", "Dấu Gió"), "status.armor_crack": ("Armor Crack", "Nứt Giáp"), "status.frozen": ("Frozen", "Đóng Băng"),
    "status.stun": ("Stunned", "Choáng"), "status.exposed": ("Exposed", "Lộ Sơ Hở"), "status.adapt": ("Adapted", "Thích Nghi"),
    # --- elements, roles, stats, rarities
    "element.fire": ("Fire", "Lửa"), "element.water": ("Water", "Nước"), "element.lightning": ("Lightning", "Sét"), "element.ice": ("Ice", "Băng"),
    "element.wind": ("Wind", "Gió"), "element.earth": ("Earth", "Đất"), "element.none": ("Physical", "Vật lý"),
    "role.guardian": ("Guardian", "Hộ Vệ"), "role.mage": ("Mage", "Pháp Sư"), "role.bruiser": ("Bruiser", "Đấu Sĩ"), "role.assassin": ("Assassin", "Sát Thủ"),
    "role.support": ("Support", "Hỗ Trợ"), "role.healer": ("Healer", "Hồi Máu"), "role.ranger": ("Ranger", "Xạ Thủ"), "role.controller": ("Controller", "Khống Chế"),
    "stat.max_hp": ("max HP", "HP tối đa"), "stat.attack": ("Attack", "Công"), "stat.defense": ("Defense", "Thủ"), "stat.attack_interval": ("attack speed", "tốc đánh"),
    "stat.range": ("range", "tầm đánh"), "stat.skill_cooldown": ("skill haste", "hồi chiêu"), "stat.crit_chance": ("crit chance", "tỉ lệ chí mạng"),
    "stat.crit_multiplier": ("crit damage", "sát thương chí mạng"), "stat.elemental_mastery": ("Elemental Mastery", "Tinh Thông Nguyên Tố"),
    "stat.status_power": ("status power", "sức mạnh hiệu ứng"), "stat.threat": ("threat", "mức thu hút"), "stat.move_speed": ("move speed", "tốc chạy"),
    "stat.heal_power": ("healing power", "sức hồi phục"), "stat.damage_bonus": ("damage", "sát thương"), "stat.reaction_bonus": ("reaction damage", "sát thương phản ứng"),
    "stat.damage_reduction": ("damage reduction", "giảm sát thương"), "stat.leash_radius": ("leash radius", "phạm vi canh giữ"), "stat.skill_power": ("skill power", "sức mạnh kỹ năng"),
    "rarity.common": ("Common", "Thường"), "rarity.rare": ("Rare", "Hiếm"), "rarity.epic": ("Epic", "Sử thi"), "rarity.legendary": ("Legendary", "Huyền thoại"),
    "rarity.cursed": ("Cursed", "Bị nguyền"),
    "family.combat": ("Combat", "Chiến đấu"), "family.element": ("Element", "Nguyên tố"), "family.defense": ("Defense", "Phòng thủ"), "family.chaos": ("Chaos", "Hỗn loạn"),
    "cardtype.stat": ("Stat", "Chỉ số"), "cardtype.ability_modifier": ("Ability", "Kỹ năng"), "cardtype.hero_specialization": ("Specialization", "Chuyên môn"),
    "cardtype.team_synergy": ("Team Synergy", "Cộng hưởng đội"), "cardtype.element_reaction": ("Reaction", "Phản ứng"), "cardtype.mutation": ("Mutation", "Đột biến"),
    "cardtype.cursed_pact": ("Cursed Pact", "Khế ước"),
    # --- tooltips: terminology (spec: distinguish damage / application / reaction / proc / cooldown)
    "help.damage": ("Damage: HP removed after Defense and resistance.", "Sát thương: HP bị trừ sau khi tính Thủ và kháng."),
    "help.application": ("Application: an attack leaves an element aura (gauge) that decays over ~2.5s.", "Áp nguyên tố: đòn đánh để lại hào quang nguyên tố, tan dần trong ~2.5s."),
    "help.reaction": ("Reaction: a second, different element hitting an aura triggers an effect and consumes gauge.", "Phản ứng: nguyên tố thứ hai khác loại chạm vào hào quang sẽ kích hoạt hiệu ứng và tiêu hao nguyên tố."),
    "help.proc": ("Proc: a relic or card trigger. Procs cannot start endless chains.", "Proc: kích hoạt từ di vật/thẻ. Không thể tạo chuỗi vô hạn."),
    "help.cooldown": ("Cooldown: time between skill casts; heroes cast automatically.", "Hồi chiêu: thời gian giữa hai lần dùng kỹ năng; anh hùng tự dùng."),
    "label.skill": ("Skill", "Kỹ năng"), "label.passive": ("Passive", "Nội tại"), "label.stats": ("HP {0} · ATK {1} · DEF {2} · Range {3}", "HP {0} · Công {1} · Thủ {2} · Tầm {3}"),
    "label.element_role": ("{0} · {1}", "{0} · {1}"), "label.drawback": ("Drawback", "Bất lợi"),
}


def main():
    en, vi = {}, {}

    def add(key, pair):
        if key in en:
            raise SystemExit("duplicate key " + key)
        en[key], vi[key] = pair

    for k, v in UI.items():
        add(k, v)
    for hid, h in HEROES.items():
        add("hero.%s.name" % hid, h["name"])
        add("hero.%s.title" % hid, h["title"])
        add("hero.%s.skill.name" % hid, h["skill"])
        add("hero.%s.skill.desc" % hid, h["skill_desc"])
        add("hero.%s.passive.name" % hid, h["passive"])
        add("hero.%s.passive.desc" % hid, h["passive_desc"])
    for eid, (name, desc, sname, sdesc) in EVOLUTIONS.items():
        add("evo.%s.name" % eid, name)
        add("evo.%s.desc" % eid, desc)
        add("evo.%s.skill.name" % eid, sname)
        add("evo.%s.skill.desc" % eid, sdesc)
    for pk, pair in EVO_PASSIVES.items():
        add("passive.%s.desc" % pk, pair)
    for eid, (name, desc) in ENEMIES.items():
        add("enemy.%s.name" % eid, name)
        add("enemy.%s.desc" % eid, desc)
    for aid, pair in AFFIXES.items():
        add("affix.%s.name" % aid, pair)
    for rid, (name, desc) in REACTIONS.items():
        add("reaction.%s.name" % rid, name)
        add("reaction.%s.desc" % rid, desc)
    for rid, (n_en, n_vi, d_en, d_vi) in RELICS.items():
        add("relic.%s.name" % rid, (n_en, n_vi))
        add("relic.%s.desc" % rid, (d_en, d_vi))
    for cid, (n_en, n_vi, d_en, d_vi) in CARDS.items():
        add("card.%s.name" % cid, (n_en, n_vi))
        add("card.%s.desc" % cid, (d_en, d_vi))
    for cid, pair in CARD_DRAWBACKS.items():
        add("card.%s.drawback" % cid, pair)
    for evid, (name, desc, options) in list(EVENTS.items()) + list(X.EVENTS_X.items()):
        add("event.%s.name" % evid, name)
        add("event.%s.desc" % evid, desc)
        for i, (text, drawback) in enumerate(options):
            add("event.%s.opt%d" % (evid, i), text)
            if drawback:
                add("event.%s.opt%d.drawback" % (evid, i), drawback)
    for n, (name, hint) in WAVES.items():
        add("wave.%d.name" % n, name)
        add("wave.%d.hint" % n, hint)
    for lid, pair in LANES.items():
        add("lane.%s" % lid, pair)

    # ---- post-MVP expansion
    for k, v in X.UI_X.items():
        add(k, v)
    for eid, pair in X.ELEMENT_NAMES.items():
        add("element.%s" % eid, pair)
    for sid, pair in X.STATUS_NAMES_NEW.items():
        add("status.%s" % sid, pair)
    for sid, pair in X.STATUS_DESCS.items():
        add("status.%s.desc" % sid, pair)
    for rid, (name, desc) in X.REACTIONS_X.items():
        add("reaction.%s.name" % rid, name)
        add("reaction.%s.desc" % rid, desc)
    for fid, pair in X.FIELDS.items():
        add("field.%s.name" % fid, pair)
    for nid, pair in X.PAIR_NOTES.items():
        add("pair.%s" % nid, pair)
    for hid, h in X.HEROES_X.items():
        add("hero.%s.name" % hid, h["name"])
        add("hero.%s.title" % hid, h["title"])
        add("hero.%s.skill.name" % hid, h["skill"])
        add("hero.%s.skill.desc" % hid, h["skill_desc"])
        add("hero.%s.passive.name" % hid, h["passive"])
        add("hero.%s.passive.desc" % hid, h["passive_desc"])
    for eid, (name, desc, sname, sdesc) in X.EVOLUTIONS_X.items():
        add("evo.%s.name" % eid, name)
        add("evo.%s.desc" % eid, desc)
        add("evo.%s.skill.name" % eid, sname)
        add("evo.%s.skill.desc" % eid, sdesc)
    for pk, pair in X.EVO_PASSIVES_X.items():
        add("passive.%s.desc" % pk, pair)
    for fid, pair in X.FIELDS_X.items():
        add("field.%s.name" % fid, pair)
    for eid, (name, desc) in X.ENEMIES_X.items():
        add("enemy.%s.name" % eid, name)
        add("enemy.%s.desc" % eid, desc)
    for rid, (n_en, n_vi, d_en, d_vi) in X.RELICS_X.items():
        add("relic.%s.name" % rid, (n_en, n_vi))
        add("relic.%s.desc" % rid, (d_en, d_vi))
    for cid, (n_en, n_vi, d_en, d_vi) in X.CARDS_X.items():
        add("card.%s.name" % cid, (n_en, n_vi))
        add("card.%s.desc" % cid, (d_en, d_vi))
    for tid, (name, desc) in X.TRAITS.items():
        add("trait.%s.name" % tid, name)
        add("trait.%s.desc" % tid, desc)
    for bid, (name, desc) in X.BONDS.items():
        add("bond.%s.name" % bid, name)
        add("bond.%s.desc" % bid, desc)
    for bid, (name, desc) in X.BIOMES.items():
        add("biome.%s.name" % bid, name)
        add("biome.%s.desc" % bid, desc)

    for lang, table in (("en", en), ("vi", vi)):
        with open(os.path.join(OUT, "loc_%s.json" % lang), "w", encoding="utf-8") as f:
            f.write("{\n")
            items = sorted(table.items())
            for i, (k, v) in enumerate(items):
                f.write("  %s: %s%s\n" % (json.dumps(k), json.dumps(v, ensure_ascii=False), "," if i < len(items) - 1 else ""))
            f.write("}\n")
    print("wrote %d keys per language" % len(en))


if __name__ == "__main__":
    main()
