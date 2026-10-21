package org.learningequality.Kolibri.discovery;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

public final class DiscoveredServer {

  private final String instanceId;
  private final String deviceName;
  private final String ip;
  private final int port;
  private final String prefix;
  private final boolean subsetOfUsersDevice;

  private DiscoveredServer(
      String instanceId,
      String deviceName,
      String ip,
      int port,
      String prefix,
      boolean subsetOfUsersDevice) {
    this.instanceId = instanceId;
    this.deviceName = deviceName;
    this.ip = ip;
    this.port = port;
    this.prefix = prefix;
    this.subsetOfUsersDevice = subsetOfUsersDevice;
  }

  /** Returns null when the TXT record is not a Kolibri server's. */
  public static DiscoveredServer fromTxt(Map<String, String> txt, String ip, int port) {
    return null;
  }

  public static List<DiscoveredServer> eligible(
      Collection<DiscoveredServer> found, Collection<String> ownAddresses) {
    return new ArrayList<>();
  }

  public String getInstanceId() {
    return instanceId;
  }

  public String getDeviceName() {
    return deviceName;
  }

  public String getIp() {
    return ip;
  }

  public String getBaseUrl() {
    return null;
  }
}
