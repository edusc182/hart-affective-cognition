class FeedbackData {
    private final String actionTaken;
    private final double affectiveChange;
    private final String rationale;

    public FeedbackData(String actionTaken, double affectiveChange, String rationale) {
        this.actionTaken = actionTaken;
        this.affectiveChange = affectiveChange;
        this.rationale = rationale;
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
}