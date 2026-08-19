class SensoryData {
    private final String lightLevel;
    private final double proximityToObjectMeters;

    public SensoryData(String lightLevel, double proximityToObjectMeters) {
        this.lightLevel = lightLevel;
        this.proximityToObjectMeters = proximityToObjectMeters;
    }

    public String getLightLevel() {
        return lightLevel;
    }

    public double getProximityToObjectMeters() {
        return proximityToObjectMeters;
    }

    @Override
    public String toString() {
        return "SensoryData[lightLevel=" + lightLevel
                + ", proximityToObjectMeters=" + proximityToObjectMeters + "]";
    }
}