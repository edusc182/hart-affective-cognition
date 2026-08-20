class FeedbackData {
    private final String actionTaken;
    private final double affectiveChange;
    private final String rationale;
    private final double saturationFactor;
    private final int repeatCount;
    private final double switchRate;

    public FeedbackData(String actionTaken, double affectiveChange, String rationale) {
        this(actionTaken, affectiveChange, rationale, 1.0, 0, 0.0);
    }

    /**
     * Construye el feedback incluyendo la telemetria de saturacion (Fase 3d).
     * `saturationFactor` atenua el cambio afectivo en Java; `repeatCount` y `switchRate`
     * describen el contexto de repeticion con el que se calculo el factor.
     */
    public FeedbackData(String actionTaken, double affectiveChange, String rationale,
                        double saturationFactor, int repeatCount, double switchRate) {
        this.actionTaken = actionTaken;
        this.affectiveChange = affectiveChange;
        this.rationale = rationale;
        this.saturationFactor = saturationFactor;
        this.repeatCount = repeatCount;
        this.switchRate = switchRate;
    }

    public String getActionTaken() {
        return actionTaken;
    }

    public double getAffectiveChange() {
        return affectiveChange;
    }

    public String getRationale() {
        return rationale;
    }

    public double getSaturationFactor() {
        return saturationFactor;
    }

    public int getRepeatCount() {
        return repeatCount;
    }

    public double getSwitchRate() {
        return switchRate;
    }
}