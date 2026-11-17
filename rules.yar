/*
 * rules.yar
 * ---------
 * YARA rules for the detector.
 *
 * WHY YARA: this file describes WHAT a logger artifact looks like, in a
 * portable, shareable format. Any analyst — or a real EDR like Wazuh —
 * can load the exact same rule. Your Python stays the orchestrator
 * (walking the disk, scoring, quarantining); YARA does the matching it
 * is built for.
 *
 * Edit the $sentinel string below to match the one your logger writes.
 * Make it long and unique so a content match is essentially unforgeable.
 */

rule Logger_Output_Sentinel
{
    meta:
        description = "Detects output files from the training command-logger"
        author      = "Hisham Zarour"
        category    = "educational / defensive"

    strings:
        // The unique end-of-session marker your logger writes.
        $sentinel = "===SESSION_END_7f3a9c==="  ascii wide nocase

        // A couple of softer supporting markers (tune or remove).
        $marker1  = "command_logger"            ascii wide nocase
        $marker2  = "captured input"            ascii wide nocase

    condition:
        // The sentinel alone is enough; the soft markers are backup.
        $sentinel or any of ($marker*)
}
